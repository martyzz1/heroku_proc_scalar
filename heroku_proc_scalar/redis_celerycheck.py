import sys
import os
import heroku
from pprint import pprint

CELERY_HOSTNAME = os.environ.get('CELERY_HOSTNAME', None)
assert(CELERY_HOSTNAME)

HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', None)
HEROKU_APPNAME = os.environ.get('HEROKU_APPNAME', None)

heroku_conn = heroku.from_key(HEROKU_API_KEY)
heroku_app = heroku_conn.apps[HEROKU_APPNAME]


key = 'DISABLE_CELERY_%s' % CELERY_HOSTNAME
DISABLE_CELERY = heroku_app.config[key]

pprint(heroku_app.config)

if DISABLE_CELERY and DISABLE_CELERY != '0':
    print "Celery disabled for %s exiting..." % DISABLE_CELERY
    sys.exit(0)
else:
    print "Celery enabled running..."
