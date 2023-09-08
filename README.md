# Django Convigvars

Configure your Django project in easy and readable way.

## Description

Configvars gives possibility to configure Django-based project with local file and environment variables (i.e. for Docker containers).

Environmental variables are the most important. If not set, the variables from the `local` module will be used, or if these are not present either - the default values will be used:

```
ENV > LOCAL > DEFAULT
```

## Installation

`pip install git+https://gitlab.com/marcinjn/django-configvars.git`


### Basic configuration

Add `configvars` to your `settings.INSTALLED_APPS`:

```python

INSTALLED_APPS = [
    # ...
    "configvars",
    # ...
]
```

### Extended configuration (with `local` settings module)

In your `settings.py` add these lines at the top of the file:

```python

from convigvars import config, secret, initialize

try:
    from . import local as settings_local  # you can use any module name for local settings
except ImportError:
    settings_local = object()

initialize(settings_local)
```

Create empty `local.py` module near your `settings.py` for customizing config variables.

As local config variables are specific to a local machine, consider adding `local.py` to `.gitignore`.

## Usage

### Config vars declaration

In your `settings.py` file declare configurable variables by using `config` or `secret` functions. The first one is used for regular variables, the second one - for secure variables (like passwords, secrets, etc).


```python

DATABASES = {
    "default": {
        "NAME": config("DB_NAME", "example"),   # `example` as default database name
        "USER": config("DB_USER", "postgres"),  # `postgres` as default username
        "PASSWORD": secret("DB_PASSWORD"),
        "HOST": config("DB_HOST", "localhost"), # `localhost` as default host
        "PORT": config("DB_PORT", 5432),        # `5432` as default port
    }
}
```

### Show configurable variables for your project

```bash
python manage.py configvars
```

Should result in something like that:

```
DB_NAME = 'example'
DB_USER = 'postgres'
DB_PASSWORD = None
DB_HOST = 'localhost'
DB_PORT = 5432
```

### Show only changed config variables

To show changed config variables by `local.py` or environment variables use:

```bash
python manage.py configvars --changed
```

### Adding short description to your config variables

In your `settings.py` declare `config` or `secret` with additional `desc` argument:

```python
MY_CUSTOM_VARIABLE = config("MY_CUSTOM_VARIABLE", "default_value", desc="Set's custom variable")
```

Then you can dump your config variables with descriptions:

```bash
$ python manage.py configvars --comment

MY_CUSTOM_VARIABLE = 'default_value'  # Set's custom variable
```


## Support

To ask question please create an issue.

## To do

* better support for type casts
* config vars view for Django Admin


## Contributing

You can contribute by creating issues, feature requests or merge requests.

## Authors and acknowledgment

- Marcin Nowak

## License

ISC License

Copyright (c) 2023 Marcin Nowak

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.

