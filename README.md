heroku-proc-scalar
==================

Django code side proc scalar

To use add the following line to you requirements.txt

    -e git://github.com/martyzz1/heroku_proc_scalar.py.git@HEAD#egg=heroku_proc_scalar

N.B. feel free to pick a specific commit point rather than HEAD


add the following to your django settings

    INSTALLED_APPS.append('heroku_proc_scalar')

If you wish to allow the https://github.com/martyzz1/heroku_proc_scalar_app to remote scale your celery processes you will need to add the following to your apps main urls.py

    urlpatterns += patterns('', url(r'^', include('heroku_proc_scalar.urls')))

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

