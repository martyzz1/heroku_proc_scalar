from django.conf import settings
from urlparse import urlparse, uses_netloc
from . import PROC_MAP, CONTROL_APP
from httplib import HTTPException
import redis
from celery.task.control import inspect
from celery import current_app as celery
from pprint import pprint
# Ensure built-in tasks are loaded for task_list view
import os
import time
import heroku
import iron_celery
import requests
from iron_mq import IronMQ
#import logging
#logger = logging.getLogger(__name__)

from celery.app.control import Control

uses_netloc.append('redis')

HEROKU_API_KEY = os.environ.get('HEROKU_API_KEY', False)
HEROKU_APPNAME = os.environ.get('HEROKU_APPNAME', False)
HEROKU_SCALAR_SHUTDOWN_RETRY = int(os.environ.get('HEROKU_SCALAR_SHUTDOWN_RETRY', 10))
proc_scalar_lock_db = urlparse(settings.PROC_SCALAR_DB)

if not HEROKU_API_KEY:
    print "HEROKU_API_KEY not set"

if not HEROKU_APPNAME:
    print "HEROKU_APPNAME not set"


def scale_me_down():
    heroku_conn = heroku.from_key(HEROKU_API_KEY)
    heroku_app = heroku_conn.apps[HEROKU_APPNAME]
    #pprint(heroku_app.processes)
    try:
        print "\n\n=============Scaling down normally!\n\n"
        #heroku_app.processes[CONTROL_APP].scale(0)
        heroku_app.processes[CONTROL_APP].scale(0)
        print "\n\n=============Ran normally\n\n"
    except KeyError as e:
        #this means the prc isn't running - bug in heroku api methinks
        # see http://samos-it.com/only-use-worker-when-required-on-heroku-with-djangopython/
        print e.message
        #print "\n\n=============Scaling down the hard way!\n\n"
        #heroku_conn._http_resource(method='POST', resource=('apps', heroku_app, 'ps', 'scale'), data={'type': CONTROL_APP, 'qty': 0})

    print "\n\n=============Finished scaling down\n\n"


def get_running_processes():

    c = Control()
    worker_hostnames = []
    hostnames = []
    try:
        hostnames = c.ping()
    except (HTTPException, requests.exceptions.HTTPError) as e:
        print "Looks like we had an exception to the c.ping()"
        print "Exception %s " % e
        print "Exception %s " % e.response()
        pprint(e)
        #celery.worker.control.active_queues
        d = get_celery_worker_status()
        pprint(d)
        pass

    print "Hostnames are:-\n"
    pprint(hostnames)
    for h in hostnames:
        for host, y in h.iteritems():
            worker_hostnames.append(host)

    return worker_hostnames


def get_running_celery_workers():

    heroku_conn = heroku.from_key(HEROKU_API_KEY)
    heroku_app = heroku_conn.apps[HEROKU_APPNAME]

    procs = heroku_app.processes
    for proc in procs:
        print "%s\n" % proc


def get_celery_worker_status():
    ERROR_KEY = "ERROR"
    try:
        insp = inspect()
        print "inspect is :-\n"
        pprint(insp)
        d = insp.stats()
        if not d:
            d = {ERROR_KEY: 'No running Celery workers were found.'}
    except IOError as e:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the RabbitMQ server is running.'
        d = {ERROR_KEY: msg}
    except (HTTPException, requests.exceptions.HTTPError) as e:
        d = {ERROR_KEY: str(e)}
    except ImportError as e:
        d = {ERROR_KEY: str(e)}
    return d


def shutdown_celery_processes(worker_hostnames, for_deployment='restart'):
#N.B. worker_hostname is set by -n variable in Procfile and MUST MUST MUST
#be identical to the process name. Break this and all is lost()
#We therefore can use procname and worker_hostname interchangeably
    heroku_conn = heroku.from_key(HEROKU_API_KEY)
    heroku_app = heroku_conn.apps[HEROKU_APPNAME]

    lock = redis.StrictRedis(
        host=proc_scalar_lock_db.hostname,
        port=int(proc_scalar_lock_db.port),
        db=int(proc_scalar_lock_db.path[1:]),
        password=proc_scalar_lock_db.password
    )

    c = Control()
    #pprint(worker_hostnames)
    if not len(worker_hostnames) > 0:
        worker_hostnames = []
        #print "[WARNING] No worker procnames given. I will shutdown ALL celery worker processes"
        hostnames = []
        try:
            hostnames = c.ping()
        except (HTTPException, requests.exceptions.HTTPError) as e:
            pass
        for h in hostnames:
            for host, y in h.iteritems():
                worker_hostnames.append(host)

    #pprint(worker_hostnames)

    worker_hostnames = list(set(worker_hostnames))
    worker_hostnames_to_process = []

    for hostname in worker_hostnames:
        key = "DISABLE_CELERY_%s" % hostname
        is_already_disabled = lock.get(key)
        if not for_deployment == is_already_disabled:
            if is_already_disabled == 'deployment':
                print "Celery process %s already marked as shutdown for deployment - nothing to do" % hostname
            else:
                worker_hostnames_to_process.append(hostname)
        else:
            worker_hostnames_to_process.append(hostname)

        lock.set(key, for_deployment)
        print "Shutting down %s" % hostname
        #celery.control.broadcast('shutdown', destination=[hostname])

    if len(worker_hostnames_to_process) > 0:
        celery.control.broadcast('shutdown', destination=worker_hostnames_to_process)
    else:
        return []

    wait_confirm_shutdown = True
    print "\n\n=========================================================\nWaiting for all the following celery workers to end gracefully (reach a state of crashed),\n this may take some time if they were currently running tasks....\n"
    status_str_length = 0
    counter = 0
    while(wait_confirm_shutdown):
        counter += 1
        still_up = 0
        status_line = ''
        for hostname in worker_hostnames_to_process:
            try:
                processes = heroku_app.processes[hostname]
            except KeyError:
                #print "looks like process %s has already gone" % hostname
                pass
            else:
                count = 0
                for proc in processes:
                    if not proc.state == 'crashed':
                        still_up = 1
                        count += 1
                if count > 0:
                    status_line += "%s=%d    " % (hostname, count)
            if counter % HEROKU_SCALAR_SHUTDOWN_RETRY == 0:
                if still_up == 1:
                    print "Shutdown of %s taking too long, re-issuing" % hostname
                    celery.control.broadcast('shutdown', destination=[hostname])

        if still_up == 0:
            print "\n============================================================\nAll processes are now marked as crashed\n"
            wait_confirm_shutdown = False
        else:
            if len(status_line) > status_str_length:
                status_str_length = len(status_line) + 1 + len(str(counter))
            print "\r%s %d".ljust(status_str_length) % (status_line, counter),
            #play nice to heroku api
            time.sleep(1)

    print "\n"
    #Now scale down...
    for hostname in worker_hostnames_to_process:
        disable_dyno(heroku_conn, heroku_app, hostname)
        key = 'DISABLE_CELERY_%s' % hostname
        lock.set('DISABLE_CELERY_%s' % hostname, 0)

    return worker_hostnames_to_process


def disable_dyno(heroku_conn, heroku_app, procname):
    #appname = HEROKU_APPNAME

    print "Disabling dyno %s" % procname
    try:
        heroku_app.processes[procname].scale(0)
    except KeyError:
        #this means the prc isn't running - bug in heroku api methinks
        # see http://samos-it.com/only-use-worker-when-required-on-heroku-with-djangopython/
        #heroku_conn._http_resource(method='POST', resource=('apps', appname, 'ps', 'scale'), data={'type': procname, 'qty': 0})
        #print "[WARN] if you see lots of these its likely there is a problem, but this could be caused by 2 processes trying to scale down the dyno's at the same time, the first one wins, this current process lost, i.e. the dyno was already gone"
        pass


def start_dynos(proclist):
    heroku_conn = heroku.from_key(HEROKU_API_KEY)
    heroku_app = heroku_conn.apps[HEROKU_APPNAME]

    for proc in proclist:
        start_dyno(heroku_conn, heroku_app, proc)


def start_dyno(heroku_conn, heroku_app, procname):

    print "starting dyno %s" % procname
    try:
        heroku_app.processes[procname].scale(1)
    except KeyError:
        #this means the prc isn't running - bug in heroku api methinks
        # see http://samos-it.com/only-use-worker-when-required-on-heroku-with-djangopython/
        heroku_conn._http_resource(method='POST', resource=('apps', HEROKU_APPNAME, 'ps', 'scale'), data={'type': procname, 'qty': 1})
        #print "[WARN] if you see lots of these its likely there is a problem, but this could be caused by 2 processes trying to scale down the dyno's at the same time, the first one wins, this current process lost, i.e. the dyno was already gone"
        pass


def get_redis_queue_count(active_queues):
    redis_queue_url = urlparse(settings.BROKER_URL)
    queue = redis.StrictRedis(
      host=redis_queue_url.hostname,
      port=int(redis_queue_url.port),
      db=int(redis_queue_url.path[1:]),
      password=redis_queue_url.password
    )

    if not active_queues:
        #print "[WARN] no active queues data given"
        active_queues = {}

    data = {}

    for queuename, procname in PROC_MAP.iteritems():
        length = int(queue.llen(queuename))
        #print "count %s = %s" % (queuename, length)
        #print "queuename = %s" % queuename
        #print "procname = %s" % procname
        #print "active %s = %s" % (queuename, active_queues[procname])
        if not procname in data:
            data[procname] = {'count': length, 'active': 0}
        else:
            data[procname]['count'] += length

        if procname in active_queues:
            data[procname]['active'] += active_queues[procname]

    return data


def get_ironmq_queue_count(active_queues):
    IRON_MQ_PROJECT_ID = settings.IRON_MQ_PROJECT_ID
    IRON_MQ_TOKEN = settings.IRON_MQ_TOKEN
    IRON_MQ_HOST = settings.IRON_MQ_HOST

    assert(IRON_MQ_PROJECT_ID)
    assert(IRON_MQ_TOKEN)
    assert(IRON_MQ_HOST)

    queue = IronMQ(host=IRON_MQ_HOST, project_id=IRON_MQ_PROJECT_ID, token=IRON_MQ_TOKEN)
    if not active_queues:
        print "[WARN] no active_queues data given"
        active_queues = {}

    data = {}

    for queuename, procname in PROC_MAP.iteritems():
        from pprint import pprint
        details = {}
        try:
            details = queue.getQueueDetails(queuename)
            pprint(details)
            length = details["size"]
        except (HTTPException, requests.exceptions.HTTPError) as e:
            length = 0

        print "count %s = %s" % (queuename, length)
        print "queuename = %s" % queuename
        print "procname = %s" % procname

        if not procname in data:
            data[procname] = {'count': length, 'active': 0}
        else:
            data[procname]['count'] += length

        if procname in active_queues:
            data[procname]['active'] += active_queues[procname]

    return data


def get_active_queues():
    i = inspect()
    d = i.stats()
    pprint(d)
    active = {}
    data = {}
    try:
        active = i.active()
    except (HTTPException, requests.exceptions.HTTPError) as e:
        print "Exception HTTPError %s " % e
        pass
    if active:
        for queuename in active.iterkeys():
            length = len(active[queuename])
            #print "%s => %s" % (queuename, length)
            if queuename in data:
                data[queuename] += length
            else:
                data[queuename] = length

    return data
