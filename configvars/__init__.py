import dataclasses
import importlib
import logging
import os
import typing

from django.core.exceptions import ImproperlyConfigured

__all__ = ["initialize", "config", "as_bool", "as_list", "secret"]

DEFAULT_LOCAL_SETTINGS_MODULE_NAME = "local"
default_app_config = "configvars.apps.ConfigVarsAppConfig"


log = logging.getLogger("configvars")


@dataclasses.dataclass
class ConfigVariable:
    name: str
    value: typing.Any = None
    desc: str = ""
    default: typing.Any = None


LOCAL = None
LOCAL_MODULE_IMPORT_FAILED = None
ENV_PREFIX = ""
ALL_CONFIGVARS = {}


def initialize(local_settings_module=None, env_prefix=""):
    global LOCAL, ENV_PREFIX, LOCAL_MODULE_IMPORT_FAILED

    if not local_settings_module:
        base_path = os.getenv("DJANGO_SETTINGS_MODULE").split(".")[:-1]
        base_path.append(DEFAULT_LOCAL_SETTINGS_MODULE_NAME)
        _local_settings_module = ".".join(base_path)
    else:
        _local_settings_module = local_settings_module

    try:
        LOCAL = importlib.import_module(_local_settings_module)
    except AttributeError as exc:
        raise ImproperlyConfigured(
            "Ensure that `local_settings_module` argument of `initialize()` "
            "function is a string containing a dotted module path."
        ) from exc
    except ImportError as exc:
        if local_settings_module:
            raise ImproperlyConfigured(
                f"Can't import local settings module {local_settings_module}"
            ) from exc
        else:
            LOCAL = object()
            LOCAL_MODULE_IMPORT_FAILED = _local_settings_module
    ENV_PREFIX = get_local("ENV_PREFIX", env_prefix)


def get_local(key, default=None):
    return getattr(LOCAL, key, default)


def getenv(envvar, default=None):
    return os.getenv(f"{ENV_PREFIX}{envvar}", default)


def config(var, default=None, desc=None):
    if LOCAL is None:
        initialize()
    value = getenv(var, get_local(var, default))
    ALL_CONFIGVARS[var] = ConfigVariable(
        name=var, desc=desc, value=value, default=default
    )
    return value


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


def secret(key, default=None):
    if LOCAL is None:
        initialize()
    value = getenv(key, get_local(key, default))
    if value:
        return value

    if os.path.isfile(value):
        with open(value) as f:
            return f.read()

    return None


def get_config_variables():
    return ALL_CONFIGVARS.values()
