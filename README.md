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

Set the values in [main/.env](main/.env) accordingly.

#### Interactive CLI

```py
py genenv.py
```

The above cmd will generate env vars step by step.

### Dependencies

```bash
pip install -r requirements.txt
```

### DB setup

```bash
py manage.py makemigrations
py manage.py migrate
```

### Server

```bash
py manage.py runserver 8000
```

_Port `8000` must be available._

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

See [main.strings.Code.Test](main/strings.py) for available `tagname(s)`.

```bash
coverage run --source='.' testmanage.py test
coverage report
coverage html
```

## Contribution

Try to separate changes in client side & server side code using separate branches, for efficient workflow run.
