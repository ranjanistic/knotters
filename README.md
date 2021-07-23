# Knotters

## Setup

_All commands/bash scripts should be assumed to be executed in the root of project directory, unless specified explicitly._

```bash
py setup.py
```

For initial setup.

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

or similar command depending on your system platform.

### DB setup

```bash
py manage.py makemigrations
```

```bash
py manage.py migrate
```

### Server

```bash
py manage.py runserver
```

or similar command depending on your system platform.

## Testing

```bash
set ENV=testing && py manage.py test
```

```bash
set ENV=testing && py manage.py test <appname>
```

```bash
set ENV=testing && py manage.py test --tag=<tagname>
```

```bash
set ENV=testing && coverage run --source='.' manage.py test
coverage report
coverage html
```

or similar commands depending on your system platform.

## Contribution

Try to separate changes in client side & server side code using separate branches, for efficient workflow run.
