import dataclasses
import os
import typing

__all__ = ["initialize", "config", "as_bool", "as_list", "secret"]


@dataclasses.dataclass
class ConfigVariable:
    name: str
    desc: str = ""
    default: typing.Any = None


LOCAL = object()
ENV_PREFIX = ""
ALL_CONFIGVARS = {}


def initialize(settings_local=None, env_prefix=""):
    global LOCAL, ENV_PREFIX

    LOCAL = settings_local or object()
    ENV_PREFIX = get_local("ENV_PREFIX", env_prefix)


def get_local(key, default=None):
    return getattr(LOCAL, key, default)


def getenv(envvar, default=None):
    return os.getenv(f"{ENV_PREFIX}{envvar}", default)


def config(var, default=None, desc=None):
    value = getenv(var, get_local(var, default))
    ALL_CONFIGVARS[var] = ConfigVariable(name=var, desc=desc, default=default)
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
    value = getenv(key, get_local(key, default))
    if not value:
        return value  # "" or None

    if os.path.isfile(value):
        with open(value) as f:
            return f.read()
    return value


def get_config_variables():
    return ALL_CONFIGVARS.values()
