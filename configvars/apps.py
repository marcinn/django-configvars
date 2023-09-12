import os

from django.apps import AppConfig
from django.core.checks import Warning, register


def check_local_settings(app_configs, **kwargs):
    errors = []
    from . import LOCAL_MODULE_IMPORT_FAILED

    if LOCAL_MODULE_IMPORT_FAILED:
        path = LOCAL_MODULE_IMPORT_FAILED.replace(".", os.sep) + ".py"
        errors.append(
            Warning(
                f"Local settings module is not defined nor default module "
                f"exist.\nConsider adding `{LOCAL_MODULE_IMPORT_FAILED}` "
                f"module to your project.\nFinally add `{path}` to your "
                f"`.gitignore`."
            )
        )
    return errors


class ConfigVarsAppConfig(AppConfig):
    name = "configvars"

    def ready(self):
        register(check_local_settings)
