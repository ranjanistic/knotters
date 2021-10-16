# Knotters

## Setup

_All commands/bash scripts should be assumed to be executed in the root of project directory, unless specified explicitly._

_`py` (python), `pip` (python package manager) - these cmdlets may vary depending on your system platform, therefore, act accordingly._

### Prerequisites

- Python 3.x, pip 21.x
- MongoDB connection string

Conditionally,

- A running redis server

This is required by a parallel qcluster. While the server can work without it, it depends on the cluster for particular resource eating tasks, like emailing, filesystem bulk I/O, asynchronous server requests, etc.

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
# Only if an error occurs
pip install rcssmin --install-option="--without-c-extensions"
pip install rjsmin --install-option="--without-c-extensions"
pip install django-compressor --upgrade
pip install -r requirements.txt
```

### Language Setup

```bash
py manage.py compilemessages
```

This will complie `.po` files and generate corresponding `.mo` files for multi language support.

For translatory contribution, see [TRANSLATION.md](TRANSLATION.md).

### DB setup

```bash
py manage.py makemigrations
py manage.py migrate
```

### Server

If you have a redis server running, then a qcluster can be started in a separate process,
which runs in parallel with the main server process.

```bash
py manage.py qcluster # requires redis config in .env file
```

```bash
py manage.py runserver
```

### Optionally

```bash
py genversion.py
```

Use this anytime if you want to have control over client side service worker updates. The above cmdlet will update a version tag on every execution, which is linked directly with the service worker, forcing it to emit an update via web browser.

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

For coverage report of tests

```bash
coverage run --source='.' testmanage.py test
coverage report
coverage html
```

## Footnotes

- Any push on beta branch deploys it directly to [beta.knotters.org](https://beta.knotters.org)

- Try to separate changes in client side & server side code using separate branches, for efficient workflow run.

- Try to publish the server sided changes before client side ones for better update delivery.
