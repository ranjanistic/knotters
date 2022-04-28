# Knotters

The Knotters Platform source code.

## Setup

_All commands/bash scripts should be assumed to be executed in the root of project directory, unless specified explicitly._

_`python3` (python), `pip` (python package manager) - these cmdlets may vary depending on your system platform, therefore, act accordingly._

### Prerequisites

- Python 3.9.x or above, pip 22.x or above
- MongoDB (5.0.x) connection string (mongodb://user:password@host:port/database)
- A running redis (6.x) server

### Initial setup

```bash
python3 setup.py
```

### Environment

To setup environment variables, use any one of the two following methods.

#### Manual creation

Set the values in [`main/.env`](main/.env) and [`main/.env.testing`](main/.env.testing) accordingly.

#### Interactive CLI

```py
python3 genenv.py
```

The above cmd will generate env vars step by step.

NOTE: Visit [djecrety.ir](http://djecrety.ir) to generate ```PROJECTKEY```.

### Dependencies

```bash
pip install -r requirements.txt
```

> If there's a ```Microsoft Visual c++ 14.0``` required error with installation of _rcssmin_ or related modules, then do following execution if you want to **avoid installing** ```Microsoft C++ Build Tools```

```bash
 # Only if an error occurs
pip install rcssmin --install-option="--without-c-extensions"
pip install rjsmin --install-option="--without-c-extensions"
pip install -r requirements.txt
```

### Language Setup

```bash
python3 manage.py compilemessages
```

This will complie `.po` files and generate corresponding `.mo` files for multi language support.

For translatory contribution, see [TRANSLATION.md](TRANSLATION.md).

### DB setup

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

[Mandatory] Create a superuser with email address same as `BOTMAIL` value in `.env` file, using the following

```bash
python3 manage.py createsuperuser
```
Provide aribtrary values for name and password (this superuser account is neccessary for the web application to work)

Later, create another superuser account for yourself, using the same above command.

### Server

A qcluster can be started in a separate process,
which runs in parallel with the main server process.

```bash
python3 manage.py qcluster # requires redis config in .env file
```

```bash
python3 manage.py runserver
```

## Static files

Set `STATIC_ROOT` in [`main/.env`](main/.env) and [`main/.env.testing`](main/.env.testing) (both should have same values) to the absolute path of directory where you want to load static files from `static` folder (like /var/www/knotters/static/). Make sure whichever path you set is not restricted for server by directory permissions.
Make sure that you DO NOT set the `STATIC_ROOT` as path to the `static` folder in your project directory in any way.

Then, use the following to load static files.

```bash
python3 manage.py collectstatic
```

This step should be done to prevent failing tests which depend on the presence of static files.

### Update static libraries

```bash
python3 static.py
```

This will read libraries source paths mentioned in `static.json`, and overwrite the files present.

Should only be used when static libraries need to be updated. If updated, then re-check if everything works fine on client side.

## Testing

Make sure that [`main/.env.testing`](main/.env.testing) is set appropriately.

```bash
python3 manage.py test
```

```bash
python3 manage.py test <appname>
```

```bash
python3 manage.py test --tag=<tagname>
```

For coverage report of tests

```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Optionally

```bash
python3 genversion.py
```

Use the above anytime if you want to have control over client side service worker updates. The above cmdlet will update a version tag on every execution, which is linked directly with the service worker, forcing it to emit an update via web browser.

```bash
python3 manage.py makemessages --extension=html,js
```

To generate `.po` files for translation at locale destination specified in your [`main/.env`](main/.env) file as `LOCALE_ABS_PATH`.

```bash
python3 manage.py compilemessages
```

To compile `.po` files to `.mo` files present at your `LOCALE_ABS_PATH`.

## Deployment

There are total 5 runners in the repository, hosted on our own servers. Following list explains the job of each runner.

- tester_knotters: All testing jobs run on this runner. Currently testing is limited to commits & pull requests on branch:main only. Deployment on beta.knotters.org does not uses testing for now (for no special reasons). The testing environment is separate from beta.knotters.org & knotters.org environment.

- beta_builder: Any commit which is pushed on branch:beta triggers the `beta-server.yml` action, which uses this runner to install/update dependencies and setup for beta.knotters.org environment.
- beta_knotters: Any commit which is pushed on branch:beta triggers the `beta-server.yml` action, which uses this runner to deploy latest changes on beta.knotters.org environment. This job for deployment requires the previous building job to be successful to run.

- builder_knotters: Any commit which is pushed on branch:main triggers the `main-server.yml`|`main-client.static.yml` action, which uses this runner to install/update dependencies and setup for knotters.org environment. This job for building requires the testing job to be successful to run.
- deploy_knotters: Any commit which is pushed on branch:beta triggers the `main-server.yml`|`main-client.static.yml` action, which uses this runner to deploy latest changes on knotters.org environment. This job for deployment requires the previous building job to be successful to run.

There are total 4 workflows in the repository, for different event trigger cases.

- beta-server.yml: This workflow is triggered on any commit to branch:beta for building and deployment in beta.knotters.org environment
- main-pr.yml: This workflow is triggered on any pull request to branch:main for testing in test environment.
- main-server.yml: This workflow is triggered on any commit to branch:main for testing, building and deployment in knotters.org environment, except on changes in static assets of repository, particularly the `static/` folder, as static updates are handled by `main-client-static.yml` workflow.
- main-client-static.yml: This workflow is triggered on any commit to branch:main for testing, building and deployment in knotters.org environment, but only on changes in static assets of repository, particularly the `static/` folder, as this workflow has additional tasks to release new client side version, compress and deploy new static assets, etc. Also, this workflow does not reload the knotters cluster, assuming that it does not depend on static asset changes.

## Footnotes

- Any push on beta branch deploys it directly to [beta.knotters.org](https://beta.knotters.org)

- Try to separate changes in client side & server side code using separate branches, for efficient workflow run.

- Try to publish the server sided changes before client side ones for better update delivery.

- Try to group changes in [`static`](static) directory under single commit to avoid instantaneous multiple client side updates.
