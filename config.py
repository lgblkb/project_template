from dynaconf import Dynaconf

settings = Dynaconf(
    envvar_prefix="{{cookiecutter.project_name}}".capitalize(),
    settings_files=['settings.yaml', '.secrets.yaml'],
    environments=True,
    load_dotenv=True,

)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load this files in the order.
