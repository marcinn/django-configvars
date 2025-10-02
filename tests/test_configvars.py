import os
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager
from unittest.mock import patch

import configvars
from configvars import as_bool, as_list


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
    configvars.LOCAL = None
    configvars.LOCAL_MODULE_IMPORT_FAILED = None
    configvars.ENV_PREFIX = ""
    configvars.ALL_CONFIGVARS = {}


@contextmanager
def config_value(module_name, env, key, default=None, **local_attrs):
    reset_default_config()
    with temporary_module(module_name, **local_attrs):
        with patch.dict(os.environ, env, clear=True):
            configvars.initialize(local_settings_module=module_name)
            yield configvars.config(key, default)


@contextmanager
def env_prefix_result():
    reset_default_config()
    with temporary_module("prefproj.local", FOO="local"):
        with patch.dict(os.environ, {"APP_FOO": "env", "FOO": "wrong"}, clear=True):
            configvars.initialize(
                local_settings_module="prefproj.local", env_prefix="APP_"
            )
            value = configvars.config("FOO", "default")
            yield configvars.ENV_PREFIX, value


@contextmanager
def secret_result():
    reset_default_config()
    with temporary_module("secretproj.local"):
        temp = tempfile.NamedTemporaryFile("w+", delete=False)
        try:
            temp.write("topsecret")
            temp.flush()
            with patch.dict(os.environ, {"SECRET": temp.name}, clear=True):
                configvars.initialize(local_settings_module="secretproj.local")
                value = configvars.secret("SECRET")
                yield value
        finally:
            temp.close()
            os.unlink(temp.name)


@contextmanager
def wrapper_vars():
    reset_default_config()
    with temporary_module("wrapproj.local", FOO="local"):
        with patch.dict(os.environ, {}, clear=True):
            configvars.initialize(local_settings_module="wrapproj.local")
            configvars.config("FOO", "default", desc="desc")
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
        reset_default_config()
        with self.assertRaises(configvars.ImproperlyConfigured):
            configvars.initialize(local_settings_module=123)

    def test_initialize_raises_for_missing_explicit_module(self):
        reset_default_config()
        with self.assertRaises(configvars.ImproperlyConfigured):
            configvars.initialize(local_settings_module="missing.module")

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

    def test_config_calls_initialize_when_uninitialized(self):
        reset_default_config()
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "FOO": "env"},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(configvars.config("FOO", "default"), "env")

    def test_secret_reads_file_content(self):
        with secret_result() as value:
            self.assertEqual(value, "topsecret")

    def test_secret_returns_empty_value(self):
        reset_default_config()
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": ""},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(configvars.secret("SECRET"), "")

    def test_secret_returns_non_file_value(self):
        reset_default_config()
        missing_path = os.path.join(
            tempfile.gettempdir(), "configvars_missing_secret_value"
        )
        if os.path.isfile(missing_path):
            os.unlink(missing_path)
        with patch.dict(
            os.environ,
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": missing_path},
            clear=True,
        ):
            sys.modules.pop("lazyproj", None)
            sys.modules.pop("lazyproj.local", None)
            self.assertEqual(configvars.secret("SECRET"), missing_path)

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

    def test_config_registers_variable_name(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].name, "FOO")

    def test_config_registers_variable_value(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].value, "local")

    def test_config_registers_variable_default(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].default, "default")

    def test_config_registers_variable_desc(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].desc, "desc")

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
