Setting up the Mentor Match API Server
======================================

Tested to work on Ubuntu Linux, should work on any Linux distribution.

Thanks
------
Some of this setup guide is adapted from [this DigitalOcean article](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04). Thanks!

Requirements
------------
* Python 3 or greater (tested with 3.5 and 3.6)
* PostgreSQL (either locally hosted or externally) setup with a user, password,
  and project database created.
* `virtualenvwrapper` for Python (optional, if you want project dependencies to
    be separate from other python projects)
* Git

Optional requirements if deploying on a production server:

* non-root user (e.g. `www`) with sudo access.
* `Gunicorn`
* `Nginx` 

Setup the project directory
===========================
If PostgreSQL does not yet have a database set up for Mentor Match, now is the
time to create it. Run the following command:

```
$ su - <DB_USER> -c "createdb <DB_NAME>"
```

where `<DB_USER>` is the username for the database user, and `<DB_NAME>` is the
name of the database to create (we recommend `mentormatch`).

Change to a directory where you want your project to go, and clone this
repository into that directory:

```
$ git clone https://github.com/mbellgb/syseng19-code
```

Change to the new directory, create a new virtualenv, and install the project
dependencies, where `<ENV_NAME>` is the desired name of your virtualenv.

```
$ cd syseng19-code
$ /path/to/mkvirtualenv <ENV_NAME>
...
$ workon <ENV_NAME>
(<ENV_NAME>) $ pip install -r requirements.txt
```

Setting the environment variables
---------------------------------
Copy the `.env.example` file to `.env` and open it in your text editor of
choice.

```
$ cp .env.example .env
$ vi .env
```

Set the settings accordingly.

* `DB_HOST` - the host where your database is located. If it is the same
  machine, then set it to `localhost`.
* `DB_USER` - the username to access the database. Normally this is `postgres`.
* `DB_PASS` - the password for `DB_USER`.
* `DB_NAME` - the name of the database which will contain the tables for Mentor
  Match.
* `HOSTNAME` - the domain name for the API server, if hosting it under a domain
  name. For instance, `api.example.com`.
* `SECRET_KEY` - the secret key used to generate various keys. You can just mash
  your keyboard to generate a reasonably lengthed (e.g. 20 characters) string.

Make sure that the database is running, then execute this command to create the
database tables:

`$ python3 manage.py migrate`

Now, create a superuser account. This is a user account for Mentor Match that
will let you perform administrative tasks. Execute the following command and
enter the required information:

`$ python3 manage.py createsuperuser`

Provided there are no errors, you should be able to test this server out by
running the following command:

```
$ python3 manage.py runserver
...
server is now running on http://localhost:8000
```

Press CTRL+C to stop the server.

Now, let's test that this can run using Gunicorn, the program we'll use to serve
the app:

```
gunicorn --bind 0.0.0.0:8000 mentormatch.wsgi:application
```

Press CTRL+C to stop the server.

We can now deactivate the virtualenv and setup a systemd service so that the app
runs in the background.

```
(<ENV_NAME>) $ deactivate
$ sudo vi /etc/systemd/system/gunicorn.service
```

Enter the following:

```
[Unit]
Description=gunicorn daemon
After=network.target
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=<USER>
Group=<GROUP>
WorkingDirectory=/path/to/syseng19-code
ExecStart=gunicorn --workers 3 --bind unix:/path/to/syseng19-code/mentormatch.sock mentormatch.wsgi:application

[Install]
WantedBy=multi-user.target
```

Now, start the service and enable it so that it starts automatically on startup.

```
$ sudo systemctl start gunicorn.service
$ sudo systemctl enable gunicorn.service
```

You may need to run this command to load the service file if you get errors.

```
$ sudo systemctl daemon-reload
```

Setting up Nginx to serve Mentor Match
--------------------------------------
For security reasons, we're going to use a reverse proxy, so that the Django app
can run as non-root on a non-HTTP port (in this case, 8000), and Nginx will
perform that for us. So when a user tries to access the API, they'll access
Nginx, and Nginx will reroute the request to our Gunicorn server, which is
serving the app. 

<!--
vim: textwidth=80
-->
