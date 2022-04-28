# Knotters

The Knotters Platform source code.

## Setup

_All commands/bash scripts should be assumed to be executed in the root of project directory, unless specified explicitly._

_`python3` (python), `pip` (python package manager) - these cmdlets may vary depending on your system platform, therefore, act accordingly._

### Prerequisites

- Python 3.9.x or above, pip 22.x or above
- MongoDB (5.0.x) connection string (mongodb://user:password@host:port/database)
- A running redis (6.x) server

### Environment

```bash
python3 setup.py
```

Check values in [`main/.env`](main/.env) and [`main/.env.testing`](main/.env.testing) manually as well, if not set using setup.py.

### Dependencies

```bash
pip install -r requirements.txt
```

> If there's a ```Microsoft Visual c++ 14.0``` required error with installation of _rcssmin_ or related modules, then do following execution if you want to **avoid installing Microsoft C++ Build Tools**

```bash
 # Only if an error occurs
pip install rcssmin --install-option="--without-c-extensions"
pip install rjsmin --install-option="--without-c-extensions"
pip install -r requirements.txt
```

### Database Setup

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

#### Accounts setup

Create a superuser using the same email address as `BOTMAIL` value in `.env` file, using the following

```bash
python3 manage.py createsuperuser
```

Provide aribtrary values for name and password (this superuser account is neccessary for the web application to work) as this account will be used as the bot.

Then, create another superuser account for yourself, using the same above command. This account can be used to access the administration view at `http://localhost:8000/<ADMINPATH>/`. The `<ADMINPATH>` here is an environment variable from `.env`.

### Server

Main server process

```bash
python3 manage.py runserver
```

## Static setup

Set `STATIC_ROOT` in [`main/.env`](main/.env) and [`main/.env.testing`](main/.env.testing) (both should have same values) to the absolute path of directory where you want to load static files from `static` folder (like `/var/www/knotters/static/`). Make sure whichever path you set is not restricted for server by any directory permissions.
Make sure that you DO NOT set the `STATIC_ROOT` as path to the `./static` folder in this project's directory in any way.

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

Should only be used when static libraries need to be updated. If updated, then re-check if everything from the updated libraries work fine on client side.

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

The following setups are not neccessary for the server to run, but might be required at some point.

#### Cluster setup

A `qcluster` can be started in a separate shell process, which runs in parallel with the main server process to handle time consuming tasks.

```bash
# requires redis config in .env file
python3 manage.py qcluster
```

#### Client setup

If you want to have control over client side service worker updates, the following command will create/update a version tag at [`main/__version__.py`](main/__version__.py) on every execution, which is linked directly with the service worker, forcing it to emit an update via web browser.

```bash
python3 genversion.py
```

#### Language setup

Set locale destination path in your [`main/.env`](main/.env) file as `LOCALE_ABS_PATH`.

You can clone the existing Knotters translation repository from [github.com/Knotters/knottrans](https:/github.com/Knotters/knottrans), and set the `LOCALE_ABS_PATH` as `/<local-path-to-clone>/knottrans/locale/`, after cloning and create a new branch in it, before generating/updating `.po` files in it.

To generate/update the `.po` files for translations

```bash
python3 manage.py makemessages --extension=html,js
```

To compile `.po` files to `.mo` files present at your `LOCALE_ABS_PATH`.

```bash
python3 manage.py compilemessages
```

If you are using the Knotters translation repository for translations, then create your own branch in that repository too, and commit & push the changes as well.
To actually deploy your new translations, create a pull request in that repository only after your related changes here in this repository have been successfully deployed on `branch:main`.

> **Contributing in translations repository provides you XPs on Knotters platform, if you have signed up and using the same GitHub account for both Knotters platform and committing in Knotters translation repository.**

## Deployment

There are total 5 runners in the repository, hosted on our own servers. Following list explains the job of each runner.

- tester_knotters: All testing jobs run on this runner. Currently testing is limited to commits & pull requests on branch:main only. Deployment on beta.knotters.org does not uses testing for now (for no special reasons). The testing environment is separate from beta.knotters.org & knotters.org environment. tags: `self-hosted, testing`
--
- beta_builder: Any commit which is pushed on `branch:beta` triggers the `beta-server.yml` action, which uses this runner to install/update dependencies and setup for beta.knotters.org environment. tags: `self-hosted, beta, building`
- beta_knotters: Any commit which is pushed on `branch:beta` triggers the `beta-server.yml` action, which uses this runner to deploy latest changes on beta.knotters.org environment. This job for deployment requires the previous building job to be successful to run. tags: `self-hosted, beta, deployment`
--
- builder_knotters: Any commit which is pushed on `branch:main` triggers the `main-server.yml`|`main-client.static.yml` action, which uses this runner to install/update dependencies and setup for knotters.org environment. This job for building requires the testing job to be successful to run. tags: `self-hosted, building, production`
- deploy_knotters: Any commit which is pushed on `branch:beta` triggers the `main-server.yml`|`main-client.static.yml` action, which uses this runner to deploy latest changes on knotters.org environment. This job for deployment requires the previous building job to be successful to run. tags: `self-hosted, deployment, production`

There are total 4 workflows in the repository, for different event trigger cases.

- beta-server.yml: This workflow is triggered on any commit to `branch:beta` for building and deployment in beta.knotters.org environment
--
- main-pr.yml: This workflow is triggered on any pull request to `branch:main` for testing in test environment.
--
- main-server.yml: This workflow is triggered on any commit to `branch:main` for testing, building and deployment in knotters.org environment, except on changes in static assets of repository, particularly the `static/` folder, as static updates are handled by `main-client-static.yml` workflow.
- main-client-static.yml: This workflow is triggered on any commit to `branch:main` for testing, building and deployment in knotters.org environment, but only on changes in static assets of repository, particularly the `static/` folder, as this workflow has additional tasks to release new client side version, compress and deploy new static assets, etc. Also, this workflow does not reload the knotters cluster, assuming that it does not depend on static asset changes.

## Footnotes

- Any push on beta branch deploys it directly to [beta.knotters.org](https://beta.knotters.org)

- In code documentation is present almost everywhere for every function, class, etc.

- Try to separate changes in client side & server side code using separate branches, for efficient workflow run.

- Try to publish the server sided changes before client side ones for better update delivery.

- Try to group changes in [`./static`](static) directory under single commit to avoid instantaneous multiple client side updates.
