import os
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import configvars
from configvars import Config, as_bool, as_list


@contextmanager
def temporary_module(module_name, **attrs):
    saved = {}
    created = []
    parts = module_name.split(".")
    prefix = ""
    for index, part in enumerate(parts):
        prefix = part if index == 0 else f"{prefix}.{part}"
        if prefix in sys.modules:
            saved[prefix] = sys.modules[prefix]
        else:
            module = types.ModuleType(prefix)
            if index < len(parts) - 1:
                module.__path__ = []
            sys.modules[prefix] = module
            created.append(prefix)
    module = sys.modules[module_name]
    for key, value in attrs.items():
        setattr(module, key, value)
    try:
        yield module
    finally:
        for name in created:
            if name not in saved:
                sys.modules.pop(name, None)
        for name, module in saved.items():
            sys.modules[name] = module


def reset_default_config():
    default = configvars.DEFAULT_CONFIG
    default._local_settings_module = None
    default._env_prefix = None
    default._all_configvars = {}
    default._local = None
    default._import_module_failed = False
    default._initialized = False
    configvars.LOCAL_MODULE_IMPORT_FAILED = None


@contextmanager
def config_value(module_name, env, key, default=None, **local_attrs):
    with temporary_module(module_name, **local_attrs):
        cfg = Config()
        with patch.dict(os.environ, env, clear=True):
            cfg.initialize(local_settings_module=module_name)
            yield cfg.config(key, default)


@contextmanager
def env_prefix_result():
    with temporary_module("prefproj.local", FOO="local"):
        cfg = Config()
        with patch.dict(os.environ, {"APP_FOO": "env", "FOO": "wrong"}, clear=True):
            cfg.initialize(local_settings_module="prefproj.local", env_prefix="APP_")
            value = cfg.config("FOO", "default")
            yield cfg.ENV_PREFIX, value


@contextmanager
def secret_result():
    with temporary_module("secretproj.local"):
        cfg = Config()
        temp = tempfile.NamedTemporaryFile("w+", delete=False)
        try:
            temp.write("topsecret")
            temp.flush()
            with patch.dict(os.environ, {"SECRET": temp.name}, clear=True):
                cfg.initialize(local_settings_module="secretproj.local")
                value = cfg.secret("SECRET")
                var = list(cfg.config_variables())[0]
                yield value, var
        finally:
            temp.close()
            os.unlink(temp.name)


@contextmanager
def wrapper_vars():
    reset_default_config()
    with temporary_module("wrapproj.local", FOO="local"):
        with patch.dict(os.environ, {}, clear=True):
            configvars.initialize(settings_module="wrapproj.local")
            configvars.config("FOO", "default")
            yield list(configvars.get_config_variables())


@contextmanager
def local_settings_warnings():
    reset_default_config()
    with patch.dict(
        os.environ, {"DJANGO_SETTINGS_MODULE": "warnproj.settings"}, clear=True
    ):
        sys.modules.pop("warnproj", None)
        sys.modules.pop("warnproj.local", None)
        configvars.initialize()
        from configvars.apps import check_local_settings

        yield check_local_settings(None)


class ConfigVarsTests(unittest.TestCase):
    def test_initialize_raises_for_invalid_module_type(self):
        cfg = Config()
        with self.assertRaises(configvars.ImproperlyConfigured):
            cfg.initialize(local_settings_module=123)

    def test_initialize_raises_for_missing_explicit_module(self):
        cfg = Config()
        with self.assertRaises(configvars.ImproperlyConfigured):
            cfg.initialize(local_settings_module="missing.module")

    def test_config_precedence_env_over_local(self):
        with config_value(
            "testproj.local", {"FOO": "env"}, "FOO", "default", FOO="local"
        ) as value:
            self.assertEqual(value, "env")

    def test_config_precedence_local_over_default(self):
        with config_value("testproj.local", {}, "FOO", "default", FOO="local") as value:
            self.assertEqual(value, "local")

    def test_config_precedence_default_used(self):
        with config_value("testproj.local", {}, "BAR", "default", FOO="local") as value:
            self.assertEqual(value, "default")

    def test_env_prefix_property(self):
        with env_prefix_result() as (prefix, _):
            self.assertEqual(prefix, "APP_")

    def test_env_prefix_config_value(self):
        with env_prefix_result() as (_, value):
            self.assertEqual(value, "env")

    def test_local_calls_initialize_when_uninitialized(self):
        cfg = Config()
        with patch.dict(
            os.environ, {"DJANGO_SETTINGS_MODULE": "lazyproj.settings"}, clear=True
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(cfg.local("FOO", "default"), "default")

    def test_env_calls_initialize_when_uninitialized(self):
        cfg = Config()
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "FOO": "env"},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(cfg.env("FOO", "default"), "env")

    def test_config_calls_initialize_when_uninitialized(self):
        cfg = Config()
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "FOO": "env"},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(cfg.config("FOO", "default"), "env")

    def test_secret_reads_file_content(self):
        with secret_result() as (value, _):
            self.assertEqual(value, "topsecret")

    def test_secret_registers_name(self):
        with secret_result() as (_, var):
            self.assertEqual(var.name, "SECRET")

    def test_secret_marks_secret(self):
        with secret_result() as (_, var):
            self.assertTrue(var.secret)

    def test_secret_value_is_hidden(self):
        with secret_result() as (_, var):
            self.assertIsNone(var.value)

    def test_secret_calls_initialize_when_uninitialized(self):
        cfg = Config()
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": "plain"},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(cfg.secret("SECRET"), "plain")

    def test_secret_returns_empty_value(self):
        cfg = Config()
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": ""},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(cfg.secret("SECRET"), "")

    def test_secret_returns_non_file_value(self):
        cfg = Config()
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": "notafile"},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(cfg.secret("SECRET"), "notafile")

    def test_as_list_splits_string(self):
        self.assertEqual(as_list("a,b"), ["a", "b"])

    def test_as_list_passthrough_list(self):
        self.assertEqual(as_list(["a", "b"]), ["a", "b"])

    def test_as_list_none_returns_empty(self):
        self.assertEqual(as_list(None), [])

    def test_as_bool_true_for_one(self):
        self.assertTrue(as_bool("1"))

    def test_as_bool_returns_bool_input(self):
        self.assertTrue(as_bool(True))

    def test_as_bool_false_for_zero(self):
        self.assertFalse(as_bool("0"))

    def test_as_bool_false_for_false_string(self):
        self.assertFalse(as_bool("false"))

    def test_as_bool_true_for_other_strings(self):
        self.assertTrue(as_bool("anything"))

    def test_initialize_wrapper_registers_name(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].name, "FOO")

    def test_initialize_wrapper_registers_value(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].value, "local")

    def test_secret_wrapper_returns_value(self):
        reset_default_config()
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": "plain"},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(configvars.secret("SECRET"), "plain")

    def test_check_local_settings_warning_count(self):
        with local_settings_warnings() as warnings:
            self.assertEqual(len(warnings), 1)

    def test_check_local_settings_warning_message(self):
        with local_settings_warnings() as warnings:
            self.assertIn("warnproj.local", warnings[0].msg)

    def test_appconfig_ready_registers_check(self):
        from configvars import apps as config_apps

        with patch.object(config_apps, "register") as register_mock:
            config_apps.ConfigVarsAppConfig("configvars", config_apps).ready()
            self.assertTrue(register_mock.called)


class DualPrefixConfigTests(unittest.TestCase):
    def setUp(self):
        self._saved_modules = {}
        for name in ("dualproj", "dualproj.local"):
            if name in sys.modules:
                self._saved_modules[name] = sys.modules[name]

        if "dualproj" not in sys.modules:
            module = types.ModuleType("dualproj")
            module.__path__ = []
            sys.modules["dualproj"] = module

        if "dualproj.local" not in sys.modules:
            mod_local = types.ModuleType("dualproj.local")
            setattr(mod_local, "FOO", "default_bar")
            sys.modules["dualproj.local"] = mod_local

        self._env_patcher = patch.dict(
            os.environ, {"APP_FOO": "alpha", "OTHER_FOO": "beta"}, clear=True
        )
        self._env_patcher.start()

        self._cfg_first = Config()
        self._cfg_first.initialize(
            local_settings_module="dualproj.local", env_prefix="APP_"
        )
        self._cfg_second = Config()
        self._cfg_second.initialize(
            local_settings_module="dualproj.local", env_prefix="OTHER_"
        )
        self._cfg_third = Config()
        self._cfg_third.initialize(
            local_settings_module="dualproj.local", env_prefix="MISSING_"
        )

    def tearDown(self):
        self._env_patcher.stop()

        for name in ("dualproj.local", "dualproj"):
            if name not in self._saved_modules:
                sys.modules.pop(name, None)
        for name, module in self._saved_modules.items():
            sys.modules[name] = module

    def test_using_prefixed_env_var_from_config(self):
        value = self._cfg_first.config("FOO")
        self.assertEqual(value, "alpha")

    def test_using_prefixed_env_var_from_second_config(self):
        value = self._cfg_second.config("FOO")
        self.assertEqual(value, "beta")

    def test_using_local_module_value_for_missing_prefix(self):
        value = self._cfg_third.config("FOO")
        self.assertEqual(value, "default_bar")
