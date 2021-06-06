# Knotters

## Setup

### Environment

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
