heroku-proc-scalar
==================

Django code side process scalar


Synopsis
========
This code basically provides 2 pieces of functionlity

    1. Fab tasks to safely shutdown your Celery worker processes, bypassing Heroku's built in 10s SIGKILL
    2. a json response providing some investigation of your celery worker processes current status. This is used by the heroku_proc_scalar_app to determine what actions to take for your app.


Usage
=====

To use add the following line to you requirements.txt

    -e git://github.com/martyzz1/heroku_proc_scalar.git@HEAD#egg=heroku_proc_scalar

N.B. feel free to pick a specific commit point rather than HEAD


add the following to your django settings

    INSTALLED_APPS.append('heroku_proc_scalar')

If you wish to allow the https://github.com/martyzz1/heroku_proc_scalar_app to remote scale your celery processes you will need to add the following to your apps main urls.py

    urlpatterns += patterns('', url(r'^', include('heroku_proc_scalar.urls')))

You must also add the included fab commands to your main app's fabfile.py

    from heroku_proc_scalar.fabfile import shutdown_celery_process, shutdown_celery_process_for_deployment

Environment settings
====================

HEROKU_API_KEY
--------------
Set your Heroku API Key as a config Variable inside your app

    heroku config:set HEROKU_API_KEY=<your key> --app <your appname>

HEROKU_APPNAME
--------------
Create a config key specifying the name of your app. This is so that the heroku.py api can be used internally to remote control you processes

    heroku config:set HEROKU_APPNAME=<your appname>

PROCFILE (optional)
--------
You can use this Environment variable to specify the Procfile you use for your system. In this way your local dev environment could use a different Procfile, and then you could set

    heroku config:set PROCFILE=./Procfile.dev

It defaults to './Procfile'

PROC_SCALAR_LOCK_DB
------------
This is used to globally controil your processes

    PROC_SCALAR_LOCK_DB='redis://redis.dev.local:6379/0'


PROCFILE
========

In order to use the heroku_proc_scalar you must configure your celery processes in the following way.
The rules of thumb are

    1. Your procname must be assigned a worker hostname via the -n option which is identical to your procname
    2. You must specify an env variable of CELERY_HOSTNAME which has the same value you used in 1. for each process
    3. You *must* use the -Q, or --queues option to specify which queues your Proc handles
    4. You *must* use the -I  heroku_proc_scalar.redis_celerycheck for each proc you wish to manage

e.g.

    <procname>: env CELERY_HOSTNAME=<procname> python manage.py celeryd -E --loglevel=DEBUG -n <procname> --queues default -I heroku_proc_scalar.redis_celerycheck

i.e.
    celery_default: CELERY_HOSTNAME=celery_default python manage.py celeryd -E --loglevel=DEBUG -n celery_default --queues default -I heroku_proc_scalar.redis_celerycheck


N.B. Using this code to control celery process on a local dev branch is NOT supported, as the whole point of this is to use heroku's api to control heroku instances.
The PROCFILE env var is simply a conveniance to aid in some elements of debug, testing and development.
