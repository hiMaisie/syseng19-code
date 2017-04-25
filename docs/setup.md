Setting up the Mentor Match API Server
======================================

Tested to work on Ubuntu Linux, should work on any Linux distribution.

Contents
========
Requirements

Install instructions

Registering an OAuth application

Questions?

Thanks
======
Some of this setup guide is adapted from [this DigitalOcean article](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-16-04). Thanks!

Requirements
============
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

Install instructions
====================

Setup the project directory
---------------------------
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
serving the app. We'll change to the root user for most of these commands, so
that we don't need to constantly have to use sudo, and then edit a new sites
config file:

```
$ sudo su
# vi /etc/nginx/sites-available/mentormatch
```

Enter the following:
```
server {
    listen 80;
    server_name <APP_URL>;

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/syseng19-code/mentormatch.sock;
    }
}
```

Make sure you replace `<APP_URL>` with either the URL you are hosting the app on
(e.g. api.example.com), or the IP address of your server.

Now we'll enable this site by symlinking it to the `sites-enabled` directory:

```
# ln -s /etc/nginx/sites-available/mentormatch /etc/nginx/sites-enabled/mentormatch
```

Test it to make sure it works:

```
# nginx -t
```

If there's no errors, then you can restart Nginx!

```
# systemctl restart nginx.service
# exit
```

As long as your firewall is correctly configured, you should now see the app by
going to the IP address or the domain name you're hosting your app on.

```
curl http://<MY_APP_URL>/tags
HTTP/1.1 200 OK
Server: nginx/1.10.0 (Ubuntu)
...
```

You can use the `/admin` endpoint to access the admin site, where you're able to
review users and other information about your app.

Further steps
-------------
* Set up encrypted HTTPS to protect you and your users from man-in-the-middle
  attacks. [link](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-16-04)
* Register an OAuth application (e.g. the Mentor Match app) with your server
  (read below)

Register an OAuth application.
==============================
Mentor Match usees OAuth2 to authenticate users and applications, thus protecting
the system from unauthorised access and use. The Mentor Match app uses OAuth to
access the app, and you can also use this system to register your own, custom
app or project.

To get started, navigate to `/auth/applications` and log in with your admin
account. You'll then be taken to a screen with a list of the apps you've
registered. Click the "New Application" button to begin creating a new
application.

Fill in the form depending on how your app works. Here's a quick guide:

* `Name`: The name of your app. This is used on the OAuth management site to
  identify your app.
* `Client id`: the unique id that represents your app. It's better to leave this
  as it is.
* `Client secret`: the secret key that's used to authenticate your app. Think of
  it as a password for your application. **Do not share this or put it onto a
  version control system**, this should remain secret. The key should have a high
  amount of entropy so you don't need to change this.
* `Client type`: "Confidential" means that the server will only suggest that the
  application exists if the secret is given correctly. Leave this as "public" if
  you're using Postman.
* `Authorization type`: Most likely, you'll use either "authorization code" or
  "implicit".
    * `Authorization code`: The user is taken to a webpage where they're
      prompted to sign in with their credentials, then they are asked if they
      want to give your application permission to perform various operations.
      Preferred method for webapps.
    * `Implicit`: The user receives no prompts whatsoever, this should be used
      for text-based apps or mobile apps where a web browser would be
      unsuitable, or your app is being hosted locally.
* `Redirect uris`: used for the authorization code flow. The uri to send the
  authorization code to.

You should read the following to find out more about how OAuth works with
applications:

* [Implicit grant](http://oauthlib.readthedocs.io/en/latest/oauth2/grants/implicit.html)
* [Authorization code grant](http://oauthlib.readthedocs.io/en/latest/oauth2/grants/authcode.html)

You can then use the client id and secret in your app. Good job! Keep in mind
these URLs, you may need them when performing OAuth operations:

* `/auth/token/` - used to generate tokens and refresh expired tokens.
* `/auth/authorize/` - used for users to sign in and generate an authorization
  code. Will redirect to your redirect uri once the flow is complete.

Our OAuth2 implementation can accept an access token in the Authorization
header, as per standard OAuth2:

```
HTTP/1.1
GET /user/me/
...
Authorization: Bearer <YOUR_AUTH_TOKEN>
...
```

Questions?
==========
Feel free to contact us by creating a new issue in this repository. We hope you
enjoy using Mentor Match.

<!--
vim: textwidth=80
-->
