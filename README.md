# Knotters

The Knotters Platform source code.

See [CONTRIBUTING.md](CONTRIBUTING.md) if you have read the whole README.md and have already setup the repository as instructed in this file. If not, then go through the following steps first, then jump to [CONTRIBUTING.md](CONTRIBUTING.md) for further contribution guidelines.

- हिंदी में रीडमी [यहां पढ़ें](रीडमी.md)
- You can contribute too by adding Readme.md in another language

Join the internal communications channel on our own [Knotters Discord Server](https://discord.gg/ZxbY6GgCES) for discussions.

## Setup

Linux environment is preferred, so if you were planning to boot/dual boot your pc with linux, this is the right time.

For windows developers who don't want to boot linux, [setup WSL](https://docs.microsoft.com/en-us/windows/wsl/install) first.

_All commands/bash scripts should be assumed to be executed in the root of project directory, unless specified explicitly._

_`python3` (python), `pip` (python package manager) - these cmdlets may vary depending on your system platform, therefore, act accordingly._

### Prerequisites

- Python 3.8.x or above
- pip 20.x or above
- MongoDB (5.0.x) connection string (mongodb://user:password@host:port/database)
- A running redis (6.x or above) server

For setting up mongodb first time locally, check [these steps](https://www.digitalocean.com/community/tutorials/how-to-install-mongodb-on-ubuntu-18-04-source)


For setting up redis first time locally, check [these steps](https://www.digitalocean.com/community/tutorials/how-to-install-and-secure-redis-on-ubuntu-18-04)

For WSL users, commands like `systemctl` may not be present, therefore proceed accordingly. (E.g. use `service` command for `systemctl`)

After setting up redis, add a user&password pair in acl section in your redis configuration file (typically at /etc/redis/redis.conf), by adding the following line in it

```conf
user <username> on ><password> allkeys allcommands
```

Restart redis after any changes to its configuration.

Make sure mongodb is running, using

```bash
mongosh "mongodb://localhost:27017/"
...
test>
```
Make sure redis is running using

```bash
redis-cli
127.0.0.1:6379> auth <user> <password>
```

### Environment

```bash
cd ~
mkdir Knotters
cd ~/Knotters
git clone <repo-clone-url>
cd ~/Knotters/knotters
python3 setup.py
```

Check values in [`main/.env`](main/.env) and [`main/.env.testing`](main/.env.testing) manually as well for everything is ok or not.

### Dependencies

```bash
pip install wheel
```

Create a python virtual environment

```bash
cd ~/Knotters
python3 -m venv knottersenv
```

Activate it

```bash
source ~/Knotters/knottersenv/bin/activate
```

Then install dependencies

```bash
cd ~/Knotters/knotters
pip install -r requirements.txt
```

### Static setup

Set `STATIC_ROOT` in [`main/.env`](main/.env) and [`main/.env.testing`](main/.env.testing) (both should have same values for this) to the absolute path of an empty directory (like `/var/www/knotters/static/`) where you can allow server to load static files from the `static` folder. 
Make sure whichever path you set is not restricted for server by any directory permissions.
Also make sure that you DO NOT set the `STATIC_ROOT` as path to the `./static` folder in this project's directory in any way.

For example, if you set `STATIC_ROOT` as `/var/www/knotters/static/`, then run

```bash
sudo mkdir -p /var/www/knotters/static/
sudo chown -R <user>:<user> /var/www/knotters/
```

Then, use the following to load static files.

```bash
python3 genversion.py
python3 manage.py collectstatic
```

This will prevent tests from failing which depend on the presence of static files at your `STATIC_ROOT` location.

You can also run the follwing to compress the collected static files at your `STATIC_ROOT`, although it is not neccessary for development/testing process.

```bash
python3 manage.py preparestatics /var/www/knotters/errors/
```

### Database Setup

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

These will create collections in your `DB_NAME` named value in .env, as database of your MongoDB server.

If the above commands are failing for you due to some kind of database error, then you can follow the steps below to fix the issue.

```bash
python3 manage.py makemigrations
python3 manage.py migrate --fake
```

### Initial setup

Create default necessary records

```bash
python3 manage.py setup
```

### Notification setup

Synchronise your database with notifications data from the source code

```bash
python3 manage.py syncnotifications
```

### Accounts setup

Create a superuser account for yourself.

```bash
python3 manage.py createsuperuser
```

This account can be used to login and access the administration view as well, at `http://localhost:8000/<ADMINPATH>/`. The `<ADMINPATH>` here is an environment variable from your `.env`.

## Server

Change your working branch (always create any new branch from `branch:beta`)

```bash
git checkout beta
git pull
git checkout -b <your-branch-name>
git status
```

Activate environment if not activated

```bash
source ~/Knotters/knottersenv/bin/activate
```

Then run the main server process (assuming port 8000 is free)

```bash
python3 manage.py runserver
```

You're now eligible to jump into [CONTRIBUTING.md](CONTRIBUTING.md), but it is recommended only after reading the complete README.md first.

## Testing

Make sure that [`main/.env.testing`](main/.env.testing) is set appropriately.

**NOTE: BEFORE RUNNING TESTS, PLEASE REMOVE ALL REDIS RELATED VALUES FROM YOUR `main/.env.testing` FILE.**

```bash
python3 manage.py test
```

```bash
python3 manage.py test <module-name>
```

```bash
python3 manage.py test --tag=<tagname>
```

```bash
python3 manage.py test --parallel --verbosity=2
```

For coverage report of tests

```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

## Optionally

The following setups are not neccessary for the server to run, but might be required at some point, so it is recommended to go through the following too.

### Cluster setup

A `qcluster` can be started in a separate shell process, which runs in parallel with the main server process to handle time consuming tasks.

```bash
# requires redis config in .env file
python3 manage.py qcluster
```

### Client setup

If you want to have control over client side service worker updates, the following command will create/update a version tag at [`main/__version__.py`](main/__version__.py) on every execution, which is linked directly with the service worker, forcing it to emit an update via web browser.

```bash
python3 genversion.py
```

### Static Libraries Update

This should only be used when static libraries need to be updated. If updated, then re-check if everything from the updated libraries work fine on client side.

```bash
python3 static.py
```

This will read libraries source paths mentioned in `static.json`, and overwrite the library files present. You should also add the update source for any new client side libraries you may use, in this file.

### Language setup

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

**✨ If you have signed up on Knotters platform and using the same GitHub account linked with it and committing in Knotters translation repository, then contributing in our translations repository provides you XPs on Knotters platform too, as it is a part of a [verified project](https://knotters.org/projects/@knottrans) on [knotters.org](https://knotters.org) itself! ✨**

## Deployment

All workflows are kept in `.github/workflows/` directory.

There are total 4 workflows in the repository, for different event trigger cases.

- beta-server.yml: This workflow is triggered on any commit to `branch:beta` for building and deployment in beta.knotters.org environment

--

- main-pr.yml: This workflow is triggered on any pull request to `branch:main` for testing in test environment.

--

- main-server.yml: This workflow is triggered on any commit to `branch:main` for testing, building and deployment in knotters.org environment, except on changes in static assets of repository, particularly the `static/` folder, as static updates are handled by `main-client-static.yml` workflow.
- main-client-static.yml: This workflow is triggered on any commit to `branch:main` for testing, building and deployment in knotters.org environment, but only if changes are restricted to static assets of repository, particularly the `static/` folder, as this workflow has additional tasks to release new client side version, compress and deploy new static assets, etc. Also, this workflow does not reload the knotters cluster, assuming that cluster does not depend on static asset changes. Also, **please make sure that any changes to contents or code in `static/` directory are deployed on a single commit at once, to avoid multiple triggering of client side static updates release caused by separate commits for the same.**

There are total 5 runners in the repository, hosted on our own servers, for the above workflows do their jobs. Following list explains the job of each runner.

- tester_knotters: All testing jobs run on this runner. Currently testing is limited to commits & pull requests on branch:main only. Deployment on beta.knotters.org does not uses testing for now (for no special reasons). The testing environment is separate from beta.knotters.org & knotters.org environment. tags: `self-hosted, testing`

--

- beta_builder: Any commit which is pushed on `branch:beta` triggers the `beta-server.yml` action, which uses this runner to install/update dependencies and setup for beta.knotters.org environment. tags: `self-hosted, beta, building`
- beta_knotters: Any commit which is pushed on `branch:beta` triggers the `beta-server.yml` action, which uses this runner to deploy latest changes on beta.knotters.org environment. This job for deployment requires the previous building job to be successful to run. tags: `self-hosted, beta, deployment`

--

- builder_knotters: Any commit which is pushed on `branch:main` triggers the `main-server.yml`|`main-client.static.yml` action, which uses this runner to install/update dependencies and setup for knotters.org environment. This job for building requires the testing job to be successful to run. tags: `self-hosted, building, production`
- deploy_knotters: Any commit which is pushed on `branch:main` triggers the `main-server.yml`|`main-client.static.yml` action, which uses this runner to deploy latest changes on knotters.org environment. This job for deployment requires the previous building job to be successful to run. tags: `self-hosted, deployment, production`

## Footnotes

- Any push on beta branch deploys it directly to [beta.knotters.org](https://beta.knotters.org)

- In code documentation is present almost everywhere for every function, class, etc.

- Try to separate changes in client side & server side code using separate branches, for efficient workflow run.

- Try to publish the server sided changes before client side ones for better update delivery.

- Try to group changes in [`./static`](static) directory under single commit to avoid instantaneous multiple client side updates. 

Jump to [CONTRIBUTING.md](CONTRIBUTING.md) for detailed contribution guide now.
