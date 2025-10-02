import dataclasses
import importlib
import logging
import os
import typing

from django.core.exceptions import ImproperlyConfigured

__all__ = [
    "initialize",
    "config",
    "as_bool",
    "as_list",
    "secret",
    "get_config_variables",
]

DEFAULT_LOCAL_SETTINGS_MODULE_NAME = "local"
default_app_config = "configvars.apps.ConfigVarsAppConfig"


log = logging.getLogger("configvars")


@dataclasses.dataclass
class ConfigVariable:
    name: str
    value: typing.Any = None
    desc: str = ""
    default: typing.Any = None
    secret: bool = False


class Config:
    def __init__(self):
        self._local_settings_module = None
        self._env_prefix = None
        self._all_configvars = {}
        self._local = None
        self._import_module_failed = False
        self._initialized = False

    @property
    def ENV_PREFIX(self):
        return self._env_prefix or ""

    def initialize(self, local_settings_module=None, env_prefix=None):
        self._initialized = False
        self._import_module_failed = False

        if env_prefix is not None:
            self._env_prefix = env_prefix

        if not local_settings_module:
            base_path = os.getenv("DJANGO_SETTINGS_MODULE").split(".")[:-1]
            base_path.append(DEFAULT_LOCAL_SETTINGS_MODULE_NAME)
            self._local_settings_module = ".".join(base_path)
        else:
            self._local_settings_module = local_settings_module

        try:
            self._local = importlib.import_module(self._local_settings_module)
        except AttributeError as exc:
            raise ImproperlyConfigured(
                "Ensure that `settings_module` argument of `__init__()` "
                "function is a string containing a dotted module path."
            ) from exc
        except ImportError as exc:
            if local_settings_module:  # if provided explicite
                raise ImproperlyConfigured(
                    f"Can't import local settings module " f"{local_settings_module}"
                ) from exc
            else:
                self._local = object()
                self._import_module_failed = self._local_settings_module
                self._initialized = True
        else:
            # backward compatibility
            self._initialized = True

    def local(self, key, default=None):
        if not self._initialized:
            self.initialize()
        return getattr(self._local, key, default)

    def env(self, key, default=None):
        if not self._initialized:
            self.initialize()
        return os.getenv(f"{self.ENV_PREFIX}{key}", default)

    def config(self, key, default=None, desc=None):
        if not self._initialized:
            self.initialize()
        value = self.env(key, self.local(key, default))
        self._all_configvars[key] = ConfigVariable(
            name=key, desc=desc, value=value, default=default
        )
        return value

    def secret(self, key, default=None, desc=None):
        if not self._initialized:
            self.initialize()
        value = self.env(key, self.local(key, default))
        self._all_configvars[key] = ConfigVariable(
            name=key, desc=desc, default=default, secret=True
        )
        if not value:
            return value  # "" or None

        if os.path.isfile(value):
            with open(value) as f:
                return f.read()
        return value

    def config_variables(self):
        return self._all_configvars.values()


def as_list(value, separator=","):
    if value:
        if isinstance(value, (list, tuple)):
            return value
        else:
            return value.split(separator)
    else:
        return []


def as_bool(value):
    if isinstance(value, bool):
        return value
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        value_str = str(value)
        if value_str.lower() in ("false", "off", "disable"):
            return False
        else:
            return True


DEFAULT_CONFIG = Config()


def initialize(settings_module=None, env_prefix=None):
    return DEFAULT_CONFIG.initialize(
        local_settings_module=settings_module, env_prefix=env_prefix
    )


def config(var, default=None, desc=None):
    return DEFAULT_CONFIG.config(key=var, default=default, desc=desc)


def secret(var, default=None, desc=None):
    return DEFAULT_CONFIG.secret(key=var, default=default, desc=desc)


def get_config_variables():
    return DEFAULT_CONFIG.config_variables()
