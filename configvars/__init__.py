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
_MISSING = object()
MASKED_SECRET_VALUE = "*****"
MAX_SECRET_FILE_SIZE = 64 * 1024


@dataclasses.dataclass
class ConfigVariable:
    name: str
    value: typing.Any = None
    desc: str = ""
    default: typing.Any = None
    secret: bool = False


class Config:
    def __init__(self):
        self._reset_state()

    def _reset_state(self):
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
        self._all_configvars = {}
        self._local = None

        self._env_prefix = env_prefix

        if not local_settings_module:
            settings_module = os.getenv("DJANGO_SETTINGS_MODULE")
            if not settings_module:
                raise ImproperlyConfigured(
                    "DJANGO_SETTINGS_MODULE environment variable is not set."
                )
            base_path = settings_module.split(".")[:-1]
            base_path.append(DEFAULT_LOCAL_SETTINGS_MODULE_NAME)
            self._local_settings_module = ".".join(base_path)
        else:
            self._local_settings_module = local_settings_module

        try:
            self._local = importlib.import_module(self._local_settings_module)
        except AttributeError as exc:
            raise ImproperlyConfigured(
                "Ensure that `local_settings_module` argument of `initialize()` "
                "is a string containing a dotted module path."
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

    def secret(
        self, key=None, default=None, desc=None, file_var=None, allow_multiline=False
    ):
        if not self._initialized:
            self.initialize()

        if key is None and file_var is None:
            raise ImproperlyConfigured("Provide `key` or `file_var` to `secret()`.")

        secret_name = key or file_var
        value = _MISSING
        file_value = _MISSING

        if key is not None:
            value = self.env(key, self.local(key, _MISSING))
        if file_var is not None:
            file_value = self.env(file_var, self.local(file_var, _MISSING))

        if value is not _MISSING and file_value is not _MISSING:
            raise ImproperlyConfigured(
                f"Set only one of `{key}` or `{file_var}` for secret `{secret_name}`."
            )

        resolved_value = default
        if file_value is not _MISSING:
            if not file_value:
                resolved_value = file_value
            else:
                if not os.path.isfile(file_value):
                    raise ImproperlyConfigured(
                        f"Secret file for `{secret_name}` does not exist: {file_value}"
                    )
                if os.path.getsize(file_value) > MAX_SECRET_FILE_SIZE:
                    raise ImproperlyConfigured(
                        f"Secret file for `{secret_name}` is too large: {file_value}"
                    )
                with open(file_value) as f:
                    resolved_value = f.read()
                if not allow_multiline and any(
                    char in resolved_value for char in ("\n", "\r")
                ):
                    raise ImproperlyConfigured(
                        f"Secret file for `{secret_name}` must be single-line."
                    )
        elif value is not _MISSING:
            resolved_value = value

        registry_value = resolved_value
        if registry_value not in (None, ""):
            registry_value = MASKED_SECRET_VALUE

        self._all_configvars[secret_name] = ConfigVariable(
            name=secret_name,
            desc=desc,
            default=default,
            value=registry_value,
            secret=True,
        )

        return resolved_value

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


default_config = Config()


def initialize(local_settings_module=None, env_prefix=None):
    return default_config.initialize(
        local_settings_module=local_settings_module, env_prefix=env_prefix
    )


def config(var, default=None, desc=None):
    return default_config.config(key=var, default=default, desc=desc)


def secret(var=None, default=None, desc=None, file_var=None, allow_multiline=False):
    return default_config.secret(
        key=var,
        default=default,
        desc=desc,
        file_var=file_var,
        allow_multiline=allow_multiline,
    )


def get_config_variables():
    return default_config.config_variables()
