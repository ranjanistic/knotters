# Knotters

## Setup

_All commands/bash scripts should be assumed to be executed in the root of project directory, unless specified explicitly._

_`py` (python), `pip` (python package manager) - these cmdlets may vary depending on your system platform, therefore, act accordingly._

### Prerequisites

- Python 3.x, pip 21.x
- MongoDB connection string

### Initial setup

```bash
py setup.py
```

### Environment

To setup environment variables, use any one of the two following methods.

#### Manual creation

Set the values in [main/.env](main/.env) and [main/.env.testing](main/.env.testing) accordingly.

#### Interactive CLI

```py
py genenv.py
```

The above cmd will generate env vars step by step.

### Dependencies

```bash
pip install -r requirements.txt
```

If there's a ```Microsoft Visual c++ 14.0``` required error with installation of _rcssmin_ or related modules of _django-compressor_, then do following execution if you want to **avoid installing** ```Microsoft C++ Build Tools```

```bash
pip install rcssmin --install-option="--without-c-extensions"
pip install rjsmin --install-option="--without-c-extensions"
pip install django-compressor --upgrade
pip install -r requirements.txt
```

### DB setup

```bash
py manage.py makemigrations
py manage.py migrate
```

### Server

```bash
py manage.py runserver
```

### Optionally

```bash
py genversion.py
```

Use this if you want to have control over client side service worker updates. The above cmd will update a version tag on every exec, which is linked directly with the service worker, forcing it to emit an update.

## Testing

Make sure that [main/.env.testing](main/.env.testing) is set appropriately.

```bash
py testmanage.py test
```

```bash
py testmanage.py test <appname>
```

```bash
py testmanage.py test --tag=<tagname>
```

See [main.strings.Code.Test](https://github.com/knottersbot/knotters/blob/7a6632741ba93fc7a62d140b9f953d8bc8084286/main/strings.py#L45) for available `tagname`(s).

For coverage report of tests

```bash
coverage run --source='.' testmanage.py test
coverage report
coverage html
```

## Contribution

Try to separate changes in client side & server side code using separate branches, for efficient workflow run.
