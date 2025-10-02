import argparse
import io
import os
import sys
import tempfile
import types
import unittest
from contextlib import contextmanager, redirect_stdout
from unittest.mock import patch

import configvars
from configvars import as_bool, as_list
from configvars.management.commands import configvars as configvars_command


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
    default = configvars.default_config
    default._reset_state()


@contextmanager
def lazy_settings_env(env):
    with patch.dict(os.environ, env, clear=True):
        sys.modules.pop("lazyproj", None)
        sys.modules.pop("lazyproj.local", None)
        yield


@contextmanager
def config_value(module_name, env, key, default=None, **local_attrs):
    with temporary_module(module_name, **local_attrs):
        cfg = configvars.default_config
        with patch.dict(os.environ, env, clear=True):
            cfg.initialize(local_settings_module=module_name)
            yield cfg.config(key, default)


@contextmanager
def env_prefix_result():
    with temporary_module("prefproj.local", FOO="local"):
        cfg = configvars.default_config
        with patch.dict(os.environ, {"APP_FOO": "env", "FOO": "wrong"}, clear=True):
            cfg.initialize(local_settings_module="prefproj.local", env_prefix="APP_")
            value = cfg.config("FOO", "default")
            yield cfg.ENV_PREFIX, value


@contextmanager
def secret_result():
    with temporary_module("secretproj.local"):
        cfg = configvars.default_config
        temp = tempfile.NamedTemporaryFile("w+", delete=False)
        try:
            temp.write("topsecret")
            temp.flush()
            with patch.dict(os.environ, {"SECRET_FILE": temp.name}, clear=True):
                cfg.initialize(local_settings_module="secretproj.local")
                value = cfg.secret("SECRET", file_var="SECRET_FILE")
                var = list(cfg.config_variables())[0]
                yield value, var
        finally:
            temp.close()
            os.unlink(temp.name)


@contextmanager
def wrapper_vars():
    cfg = configvars.default_config
    with temporary_module("wrapproj.local", FOO="local"):
        with patch.dict(os.environ, {}, clear=True):
            cfg.initialize(local_settings_module="wrapproj.local")
            cfg.config("FOO", "default", desc="desc")
            yield list(cfg.config_variables())


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


def run_command(**options):
    command = configvars_command.Command()
    output = io.StringIO()
    defaults = {"comments": False, "changed": False, "defaults": False}
    defaults.update(options)
    with redirect_stdout(output):
        command.handle(**defaults)
    return output.getvalue()


class ConfigVarsTests(unittest.TestCase):
    def setUp(self):
        reset_default_config()
        self.cfg = configvars.default_config

    def test_temporary_module_restores_saved_modules(self):
        original = types.ModuleType("savedproj")
        sys.modules["savedproj"] = original
        try:
            with temporary_module("savedproj.local"):
                pass
            self.assertIs(sys.modules["savedproj"], original)
        finally:
            sys.modules.pop("savedproj", None)

    def test_initialize_clears_config_variables(self):
        with temporary_module("wrapproj.local"):
            with patch.dict(os.environ, {}, clear=True):
                self.cfg.initialize(local_settings_module="wrapproj.local")
                self.cfg.config("FOO", "default")
                self.cfg.initialize(local_settings_module="wrapproj.local")
                self.assertEqual(len(list(self.cfg.config_variables())), 0)

    def test_command_defaults_prints_default_value(self):
        with temporary_module("cmdproj.local"):
            with patch.dict(os.environ, {}, clear=True):
                configvars.initialize(local_settings_module="cmdproj.local")
                configvars.config("FOO", "default")
                output = run_command(defaults=True)
                self.assertEqual(output.strip(), "FOO = 'default'")

    def test_command_add_arguments_registers_options(self):
        parser = argparse.ArgumentParser()
        configvars_command.Command().add_arguments(parser)
        actions = {action.dest for action in parser._actions}
        self.assertTrue({"comments", "changed", "defaults"}.issubset(actions))

    def test_command_changed_skips_unchanged_value(self):
        with temporary_module("cmdproj.local"):
            with patch.dict(os.environ, {}, clear=True):
                configvars.initialize(local_settings_module="cmdproj.local")
                configvars.config("FOO", "default")
                output = run_command(changed=True)
                self.assertEqual(output, "")

    def test_command_prints_current_value(self):
        with temporary_module("cmdproj.local", FOO="local"):
            with patch.dict(os.environ, {}, clear=True):
                configvars.initialize(local_settings_module="cmdproj.local")
                configvars.config("FOO", "default")
                output = run_command()
                self.assertEqual(output.strip(), "FOO = 'local'")

    def test_command_prints_comment(self):
        with temporary_module("cmdproj.local", FOO="local"):
            with patch.dict(os.environ, {}, clear=True):
                configvars.initialize(local_settings_module="cmdproj.local")
                configvars.config("FOO", "default", desc="desc")
                output = run_command(comments=True)
                self.assertEqual(output.strip(), "FOO = 'local'  # desc")

    def test_command_masks_secret_value_when_set(self):
        with temporary_module("cmdproj.local"):
            with patch.dict(os.environ, {"SECRET": "plain"}, clear=True):
                configvars.initialize(local_settings_module="cmdproj.local")
                configvars.secret("SECRET")
                output = run_command()
                self.assertEqual(output.strip(), "SECRET = '*****'")

    def test_command_keeps_secret_none_when_unset(self):
        with temporary_module("cmdproj.local"):
            with patch.dict(os.environ, {}, clear=True):
                configvars.initialize(local_settings_module="cmdproj.local")
                configvars.secret("SECRET")
                output = run_command()
                self.assertEqual(output.strip(), "SECRET = None")

    def test_initialize_wrapper_uses_default_config(self):
        with temporary_module("wrapproj.local", FOO="local"):
            with patch.dict(os.environ, {}, clear=True):
                configvars.initialize(local_settings_module="wrapproj.local")
                self.assertEqual(configvars.config("FOO", "default"), "local")

    def test_secret_wrapper_uses_default_config(self):
        with temporary_module("secretwrap.local"):
            with patch.dict(os.environ, {"SECRET": "plain"}, clear=True):
                configvars.initialize(local_settings_module="secretwrap.local")
                self.assertEqual(configvars.secret("SECRET"), "plain")

    def test_secret_wrapper_supports_file_var(self):
        with temporary_module("secretwrap.local"):
            temp = tempfile.NamedTemporaryFile("w+", delete=False)
            try:
                temp.write("wrapped")
                temp.flush()
                with patch.dict(os.environ, {"SECRET_FILE": temp.name}, clear=True):
                    configvars.initialize(local_settings_module="secretwrap.local")
                    self.assertEqual(
                        configvars.secret("SECRET", file_var="SECRET_FILE"), "wrapped"
                    )
            finally:
                temp.close()
                os.unlink(temp.name)

    def test_get_config_variables_wrapper_returns_values(self):
        with temporary_module("wrapproj.local", FOO="local"):
            with patch.dict(os.environ, {}, clear=True):
                configvars.initialize(local_settings_module="wrapproj.local")
                configvars.config("FOO", "default")
                self.assertEqual(len(list(configvars.get_config_variables())), 1)

    def test_initialize_requires_settings_module(self):
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(configvars.ImproperlyConfigured):
                self.cfg.initialize()

    def test_initialize_raises_for_invalid_module_type(self):
        with self.assertRaises(configvars.ImproperlyConfigured):
            self.cfg.initialize(local_settings_module=123)

    def test_initialize_raises_for_missing_explicit_module(self):
        with self.assertRaises(configvars.ImproperlyConfigured):
            self.cfg.initialize(local_settings_module="missing.module")

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

    def test_config_env_empty_overrides_local(self):
        with config_value(
            "emptyproj.local", {"FOO": ""}, "FOO", "default", FOO="local"
        ) as value:
            self.assertEqual(value, "")

    def test_env_prefix_property(self):
        with env_prefix_result() as (prefix, _):
            self.assertEqual(prefix, "APP_")

    def test_env_prefix_config_value(self):
        with env_prefix_result() as (_, value):
            self.assertEqual(value, "env")

    def test_local_calls_initialize_when_uninitialized(self):
        with lazy_settings_env({"DJANGO_SETTINGS_MODULE": "lazyproj.settings"}):
            self.assertEqual(self.cfg.local("FOO", "default"), "default")

    def test_env_calls_initialize_when_uninitialized(self):
        with lazy_settings_env(
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "FOO": "env"}
        ):
            self.assertEqual(self.cfg.env("FOO", "default"), "env")

    def test_config_calls_initialize_when_uninitialized(self):
        with lazy_settings_env(
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "FOO": "env"}
        ):
            self.assertEqual(self.cfg.config("FOO", "default"), "env")

    def test_secret_reads_file_content(self):
        with secret_result() as (value, _):
            self.assertEqual(value, "topsecret")

    def test_secret_reads_empty_file(self):
        with temporary_module("emptysecret.local"):
            temp = tempfile.NamedTemporaryFile("w+", delete=False)
            try:
                temp.flush()
                with patch.dict(os.environ, {"SECRET_FILE": temp.name}, clear=True):
                    self.cfg.initialize(local_settings_module="emptysecret.local")
                    self.assertEqual(
                        self.cfg.secret("SECRET", file_var="SECRET_FILE"), ""
                    )
            finally:
                temp.close()
                os.unlink(temp.name)

    def test_secret_reads_absolute_path_from_file_var(self):
        with temporary_module("abssecret.local"):
            temp = tempfile.NamedTemporaryFile("w+", delete=False)
            try:
                temp.write("abs")
                temp.flush()
                with patch.dict(os.environ, {"SECRET_FILE": temp.name}, clear=True):
                    self.cfg.initialize(local_settings_module="abssecret.local")
                    self.assertEqual(
                        self.cfg.secret("SECRET", file_var="SECRET_FILE"), "abs"
                    )
            finally:
                temp.close()
                os.unlink(temp.name)

    def test_secret_reads_relative_path_from_file_var(self):
        with temporary_module("relsecret.local"):
            temp = tempfile.NamedTemporaryFile("w+", delete=False)
            try:
                temp.write("rel")
                temp.flush()
                rel_path = os.path.relpath(temp.name, start=os.getcwd())
                with patch.dict(os.environ, {"SECRET_FILE": rel_path}, clear=True):
                    self.cfg.initialize(local_settings_module="relsecret.local")
                    self.assertEqual(
                        self.cfg.secret("SECRET", file_var="SECRET_FILE"), "rel"
                    )
            finally:
                temp.close()
                os.unlink(temp.name)

    def test_secret_file_var_rejects_multiline_by_default(self):
        with temporary_module("multisecret.local"):
            temp = tempfile.NamedTemporaryFile("w+", delete=False)
            try:
                temp.write("line1\nline2")
                temp.flush()
                with patch.dict(os.environ, {"SECRET_FILE": temp.name}, clear=True):
                    self.cfg.initialize(local_settings_module="multisecret.local")
                    with self.assertRaises(configvars.ImproperlyConfigured):
                        self.cfg.secret("SECRET", file_var="SECRET_FILE")
            finally:
                temp.close()
                os.unlink(temp.name)

    def test_secret_file_var_allows_multiline_when_enabled(self):
        with temporary_module("multisecret.local"):
            temp = tempfile.NamedTemporaryFile("w+", delete=False)
            try:
                temp.write("line1\nline2")
                temp.flush()
                with patch.dict(os.environ, {"SECRET_FILE": temp.name}, clear=True):
                    self.cfg.initialize(local_settings_module="multisecret.local")
                    self.assertEqual(
                        self.cfg.secret(
                            "SECRET", file_var="SECRET_FILE", allow_multiline=True
                        ),
                        "line1\nline2",
                    )
            finally:
                temp.close()
                os.unlink(temp.name)

    def test_secret_file_var_raises_when_file_too_large(self):
        with temporary_module("largesecret.local"):
            temp = tempfile.NamedTemporaryFile("w+", delete=False)
            try:
                temp.write("12345")
                temp.flush()
                with patch.object(configvars, "MAX_SECRET_FILE_SIZE", 4):
                    with patch.dict(os.environ, {"SECRET_FILE": temp.name}, clear=True):
                        self.cfg.initialize(local_settings_module="largesecret.local")
                        with self.assertRaises(configvars.ImproperlyConfigured):
                            self.cfg.secret("SECRET", file_var="SECRET_FILE")
            finally:
                temp.close()
                os.unlink(temp.name)

    def test_secret_returns_path_string_when_file_missing(self):
        with temporary_module("missingsecret.local"):
            missing = "no_such_secret_file"
            with patch.dict(os.environ, {"SECRET": missing}, clear=True):
                self.cfg.initialize(local_settings_module="missingsecret.local")
                self.assertEqual(self.cfg.secret("SECRET"), missing)

    def test_secret_file_var_raises_when_file_missing(self):
        with temporary_module("missingsecret.local"):
            with patch.dict(
                os.environ, {"SECRET_FILE": "no_such_secret_file"}, clear=True
            ):
                self.cfg.initialize(local_settings_module="missingsecret.local")
                with self.assertRaises(configvars.ImproperlyConfigured):
                    self.cfg.secret("SECRET", file_var="SECRET_FILE")

    def test_secret_supports_file_var_without_var(self):
        with temporary_module("onlyfilesecret.local"):
            temp = tempfile.NamedTemporaryFile("w+", delete=False)
            try:
                temp.write("file-only")
                temp.flush()
                with patch.dict(os.environ, {"SECRET_FILE": temp.name}, clear=True):
                    self.cfg.initialize(local_settings_module="onlyfilesecret.local")
                    self.assertEqual(
                        self.cfg.secret(file_var="SECRET_FILE"), "file-only"
                    )
            finally:
                temp.close()
                os.unlink(temp.name)

    def test_secret_returns_empty_when_file_var_is_empty(self):
        with temporary_module("emptyfilesecret.local"):
            with patch.dict(os.environ, {"SECRET_FILE": ""}, clear=True):
                self.cfg.initialize(local_settings_module="emptyfilesecret.local")
                self.assertEqual(self.cfg.secret("SECRET", file_var="SECRET_FILE"), "")

    def test_secret_raises_when_both_names_missing(self):
        with temporary_module("nonamesecret.local"):
            with patch.dict(os.environ, {}, clear=True):
                self.cfg.initialize(local_settings_module="nonamesecret.local")
                with self.assertRaises(configvars.ImproperlyConfigured):
                    self.cfg.secret()

    def test_secret_raises_when_both_sources_are_set(self):
        with temporary_module("conflictsecret.local"):
            with patch.dict(
                os.environ, {"SECRET": "plain", "SECRET_FILE": "path"}, clear=True
            ):
                self.cfg.initialize(local_settings_module="conflictsecret.local")
                with self.assertRaises(configvars.ImproperlyConfigured):
                    self.cfg.secret("SECRET", file_var="SECRET_FILE")

    def test_secret_empty_literal_conflicts_with_file_var(self):
        with temporary_module("conflictsecret.local"):
            with patch.dict(
                os.environ, {"SECRET": "", "SECRET_FILE": "path"}, clear=True
            ):
                self.cfg.initialize(local_settings_module="conflictsecret.local")
                with self.assertRaises(configvars.ImproperlyConfigured):
                    self.cfg.secret("SECRET", file_var="SECRET_FILE")

    def test_secret_registers_name(self):
        with secret_result() as (_, var):
            self.assertEqual(var.name, "SECRET")

    def test_secret_marks_secret(self):
        with secret_result() as (_, var):
            self.assertTrue(var.secret)

    def test_secret_value_is_hidden(self):
        with secret_result() as (_, var):
            self.assertEqual(var.value, "*****")

    def test_secret_calls_initialize_when_uninitialized(self):
        with lazy_settings_env(
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": "plain"}
        ):
            self.assertEqual(self.cfg.secret("SECRET"), "plain")

    def test_secret_returns_empty_value(self):
        with lazy_settings_env(
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": ""}
        ):
            self.assertEqual(self.cfg.secret("SECRET"), "")

    def test_secret_returns_non_file_value(self):
        with lazy_settings_env(
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": "notafile"}
        ):
            self.assertEqual(self.cfg.secret("SECRET"), "notafile")

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

    def test_config_registers_variable_default(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].default, "default")

    def test_config_registers_variable_desc(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].desc, "desc")

    def test_initialize_wrapper_registers_name(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].name, "FOO")

    def test_initialize_wrapper_registers_value(self):
        with wrapper_vars() as vars_list:
            self.assertEqual(vars_list[0].value, "local")

    def test_secret_wrapper_returns_value(self):
        with lazy_settings_env(
            {"DJANGO_SETTINGS_MODULE": "lazyproj.settings", "SECRET": "plain"}
        ):
            self.assertEqual(self.cfg.secret("SECRET"), "plain")

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
