PSQL backed catalog application (Flask based)
=============================================

Overview
--------
This package contains all modules, templates and static files for a catalog web application.
The application is web based and support CRUD operations on catalog items. It uses google+ authentication
for user authentication and allows for local storage of images on the server.

Structure
---------

### flask application ###
The entire application is in the included app folder. Files that will require modification to run the app are below.
All static files are in ./app/static and all html files are in ./app/templates.

* ./app/templates/login.html
    
    `data-clientid` needs to be set to the client id of a google application
    
* ./client_secrets.json needs to be downloaded from https://console.developers.google.com/ in order for google sign-in to work
as expected matching the client id above.

### database_setup.py ###

This is the file that creates the psql database tables. The database needs to be exported in DATABASE_URL environment variable.

### project.py ###

This is the script to run to run a debug server on localhost. The PORT environment variable defines the port to run on.

Running the app
---------------

The app needs to be connected to a Google application for authentication. See application structure for details on how to configure it.
Once the modifications for the google app are done, the following steps are needed to run the app locally.

1. Export psql database login information in DATABASE_URL. Example `postgres://username:pass@host:port/db_name`
2. Export port information in PORT variable. Example `export PORT=5000`
3. Run database_setup.py. `python database_setup.py`
4. Run app. `python project.py`

Requirements
------------

See runtime.txt for python version used in testing.
See requirements.txt for python modules required to run the app.

Heroku Deployment
-----------------

This app has a Procfile and configuration files for Heroku deployment. There are 2 steps needed for Heroku deployment after
initial app deployment for the app to work.

1. Postgresql needs to be added on. This can be done with the following command.

```
    heroku addons:create heroku-postgresql:hobby-dev
```
 
2. The database needs to be setup. This can be done with the 2 commands below after initial app deployment.

```
    heroku run bash
    python database_setup.py
```

Image storage
-------------

By default images are stored on local disk as defined by `UPLOADED_PHOTOS_DEST = '/app/app/static/images'` in database_setup.py.
To change the location to a different place if the app is ran in a different disk lcoation, change that configuration variable.

Catalog APIs
------------

The app supports both JSON and XML endpoints for dumping the available data

### JSON ###

![json dump](demo/json.png "JSON dump")

### XML ###

![xml dump](demo/xml.png "XML dump")

Example App
-----------

An example app is running at http://catalog-demo.herokuapp.com/ and can be used there.

![example app](demo/overall.png "Heroku app running")
