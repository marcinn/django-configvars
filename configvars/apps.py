import os

from django.apps import AppConfig
from django.core.checks import Warning, register


def check_local_settings(app_configs, **kwargs):
    errors = []
    from . import default_config

    if default_config._import_module_failed:
        path = default_config._local_settings_module.replace(".", os.sep) + ".py"
        errors.append(
            Warning(
                f"Local settings module is not defined nor default module "
                f"exist.\nConsider adding `{default_config._local_settings_module}` "
                f"module to your project.\nFinally add `{path}` to your "
                f"`.gitignore`."
            )
        )
    return errors


class ConfigVarsAppConfig(AppConfig):
    name = "configvars"

    def ready(self):
        register(check_local_settings)
