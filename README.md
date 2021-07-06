# Knotters

## Setup

_All commands/bash scripts should be assumed to be executed in the root of project directory, unless specified explicitly._

### Environment

To setup environment variables, use any one of the two following methods.

#### Interactive CLI

```py
py genenv.py
```

The above cmd will generate env vars step by step.

#### Manual creation

Copy contents of [main/.env.example](main/.env.example) to a new file at [main/.env](main/.env), and set the values in content accordingly.

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
