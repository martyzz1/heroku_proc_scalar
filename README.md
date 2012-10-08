heroku-proc-scalar
==================

Django code side proc scalar

To use add the following line to you requirements.txt

    -e git://github.com/martyzz1/heroku_proc_scalar.py.git@HEAD#egg=heroku_proc_scalar

N.B. feel free to pick a specific commit point rather than HEAD


add the following to your django settings

    INSTALLED_APPS.append('heroku_proc_scalar')

If you wish to allow the heroku_proc_scalar_app to remote scale your celery processes you will need to add the following to your apps main urls.py

    urlpatterns += patterns(r'^', include('heroku_proc_scalar.urls'))

