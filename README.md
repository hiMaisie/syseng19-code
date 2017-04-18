# syseng19-code [![Build Status](https://travis-ci.org/mbellgb/syseng19-code.svg?branch=master)](https://travis-ci.org/mbellgb/syseng19-code)
Code repository for systems engineering project.

[Live API Documentation](https://app.swaggerhub.com/api/mbellgb/mentor-match/0.2.1)

## Setting up a development environment

You'll need:
* Python 3.5 or better
* PostgreSQL with a valid user
* virtualenvwrapper

Create a new virtualenv using the virutalenvwrapper, where `$envname` is the name of your virtualenv.

```$ /path/to/mkvirtualenv $envname```

Activate it.

```$ workon $envname```

Install the dependencies.

```$ pip install -r requirements.txt```

If you haven't already, create a new database for the app. You should be using a command similar to below:

```$ su - postgres -c "createdb mentormatch"```

Copy .env.example to .env and populate it with your own values. Use some random string for SECRET_KEY.

```
$ cp .env.example .env
$ vi .env

DB_HOST=localhost
DB_USER=postgres
DB_NAME=mentormatch
DB_PASSWD=password

HOSTNAME=localhost
SECRET_KEY=";isbdd;szdbs;idfbszdjlfib"
```

Migrate the database tables.

```$ python manage.py migrate```

Run the server.

```$ python manage.py runserver```

Navigate to http://localhost:8000 and you should see the app!
