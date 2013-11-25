from __future__ import print_function
from . import PROC_MAP, QUEUE_MAP
from httplib import HTTPException
from importlib import import_module
import os
import time
import heroku
import redis
import requests
import settings

app = import_module(os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0]).celery.app

try:
    from iron_mq import IronMQ
except ImportError:
    IronMQ = None  # noqa
    #print("couldn't import iron_mq, no support for it")


def get_heroku_conn():
    assert settings.HEROKU_API_KEY
    assert settings.HEROKU_APPNAME
    heroku_conn = heroku.from_key(settings.HEROKU_API_KEY)
    return heroku_conn, heroku_conn.app(settings.HEROKU_APPNAME)


def get_running_celery_workers():
    heroku_conn, heroku_app = get_heroku_conn()
    procs = heroku_app.process_formation()
    workers = []
    for proc in procs:
        # 'app_name', 'slug', 'command', 'upid', 'process', 'action', 'rendezvous_url', 'pretty_state', 'state'
        procname = proc.type
        if proc.quantity > 0:
            if procname in QUEUE_MAP:
                workers.append(procname)
    return workers


def _get_worker_hostnames(control):
    try:
        hostnames = control.ping()
    except (HTTPException, requests.exceptions.HTTPError):
        return []
    else:
        worker_hostnames = []
        for h in hostnames:
            for host, _ in h.iteritems():
                worker_hostnames.append(host)
        return worker_hostnames


def shutdown_celery_processes(worker_hostnames, for_deployment='idle'):
    # N.B. worker_hostname is set by -n variable in Procfile and MUST MUST MUST
    # be identical to the process name. Break this and all is lost()
    # We therefore can use procname and worker_hostname interchangeably
    heroku_conn, heroku_app = get_heroku_conn()

    print("shutting down celery for " + for_deployment)

    lock = redis.StrictRedis(
        host=settings.proc_scalar_lock_url.hostname,
        port=int(settings.proc_scalar_lock_url.port),
        db=int(settings.proc_scalar_lock_url.path[1:]),
        password=settings.proc_scalar_lock_url.password
    )

    if not len(worker_hostnames) > 0:
        worker_hostnames = _get_worker_hostnames(app.control)
    worker_hostnames = list(set(worker_hostnames))
    worker_hostnames_to_process = []

    for hostname in worker_hostnames:
        key = "DISABLE_CELERY_%s" % hostname
        is_already_disabled = lock.get(key)
        if not is_already_disabled == 'deployment':
            print("locking {} for {}".format(hostname, for_deployment))
            lock.set(key, for_deployment)

        worker_hostnames_to_process.append(hostname)

    if len(worker_hostnames_to_process) > 0:
        print("broadcasting shutdown to %s" % worker_hostnames_to_process)
        print("app config %s" % app._config_source)
        app.control.broadcast('shutdown', destination=worker_hostnames_to_process)
    else:
        return []

    wait_confirm_shutdown = True
    print("Waiting for all the following celery workers to end gracefully (reach a state of crashed),"
        + " this may take some time if they were currently running tasks...")
    status_str_length = 0
    counter = 0
    while(wait_confirm_shutdown):
        counter += 1
        still_up = 0
        status_line = ''
        dynos = heroku_app.dynos()
        for proc_type in worker_hostnames_to_process:
            if proc_type in dynos:
                count = 0
                for proc in dynos[proc_type]:
                    if not proc.state == 'crashed':
                        still_up = 1
                        count += 1
                if count > 0:
                    status_line += "%s=%d    " % (proc_type, count)
            else:
                # looks like process has already gone
                pass
            if counter % settings.HEROKU_SCALAR_SHUTDOWN_RETRY == 0:
                if still_up == 1:
                    print("shutdown of {} taking too long, re-issuing".format(proc_type))
                    app.control.broadcast('shutdown', destination=[proc_type])

        if still_up == 0:
            print("all processes are now marked as crashed")
            wait_confirm_shutdown = False
        else:
            if len(status_line) > status_str_length:
                status_str_length = len(status_line) + 1 + len(str(counter))
            print("\r%s %d".ljust(status_str_length) % (status_line, counter))
            # play nice to heroku api usually takes about 10 seconds to shutdown
            time.sleep(10)

    # Now scale down...
    for hostname in worker_hostnames_to_process:
        disable_dyno(heroku_conn, heroku_app, hostname)
        # only remove the lock if we're not shutting down for deployment
        # otherwise the proc scalar wouldn't be able to restart this.
        key = "DISABLE_CELERY_%s" % hostname
        is_already_disabled = lock.get(key)
        if not for_deployment == 'deployment':
            if not is_already_disabled == 'deployment':
                print("unlocking {} from {}".format(hostname, is_already_disabled))
                lock.set(key, 0)

    return worker_hostnames_to_process


def disable_dyno(heroku_conn, heroku_app, procname):
    print("disabling dyno " + procname)
    heroku_app.scale_formation_process(procname, 0)


def lock_celery():
    lock = redis.StrictRedis(
        host=settings.proc_scalar_lock_url.hostname,
        port=int(settings.proc_scalar_lock_url.port),
        db=int(settings.proc_scalar_lock_url.path[1:]),
        password=settings.proc_scalar_lock_url.password
    )

    for procname in QUEUE_MAP.iterkeys():
        key = "DISABLE_CELERY_%s" % procname
        print("locking {} for deployment".format(procname))
        lock.set(key, 'deployment')


def unlock_celery():
    lock = redis.StrictRedis(
        host=settings.proc_scalar_lock_url.hostname,
        port=int(settings.proc_scalar_lock_url.port),
        db=int(settings.proc_scalar_lock_url.path[1:]),
        password=settings.proc_scalar_lock_url.password
    )

    for procname in QUEUE_MAP.iterkeys():
        key = "DISABLE_CELERY_%s" % procname
        print("unlocking {} after deployment".format(procname))
        lock.set(key, 0)


def start_dynos(proclist, after_deployment='idle'):
    heroku_conn, heroku_app = get_heroku_conn()

    for proc in proclist:
        start_dyno(heroku_conn, heroku_app, proc)


def start_dyno(heroku_conn, heroku_app, procname):
    print("starting dyno " + procname)
    heroku_app.scale_formation_process(procname, 1)


def get_redis_queue_count(active_queues):
    queue = redis.StrictRedis(
        host=settings.redis_queue_url.hostname,
        port=int(settings.redis_queue_url.port),
        db=int(settings.redis_queue_url.path[1:]),
        password=settings.redis_queue_url.password
    )

    lock = redis.StrictRedis(
        host=settings.proc_scalar_lock_url.hostname,
        port=int(settings.proc_scalar_lock_url.port),
        db=int(settings.proc_scalar_lock_url.path[1:]),
        password=settings.proc_scalar_lock_url.password
    )

    if not active_queues:
        active_queues = {}

    data = {}

    for queuename, procname in PROC_MAP.iteritems():
        length = int(queue.llen(queuename))
        if not procname in data:
            key = "DISABLE_CELERY_%s" % procname
            lock_type = lock.get(key)
            if not lock_type == 0:
                lock_type = 0
            data[procname] = {'count': length, 'active': 0, 'deploy_lock': lock_type}
        else:
            data[procname]['count'] += length

        if procname in active_queues:
            data[procname]['active'] += active_queues[procname]

    return data


def get_ironmq_queue_count(active_queues):
    if not IronMQ:
        return print("iron_mq not loaded, not getting queue count")
    assert(settings.IRON_MQ_PROJECT_ID)
    assert(settings.IRON_MQ_TOKEN)
    assert(settings.IRON_MQ_HOST)

    lock = redis.StrictRedis(
        host=settings.proc_scalar_lock_url.hostname,
        port=int(settings.proc_scalar_lock_url.port),
        db=int(settings.proc_scalar_lock_url.path[1:]),
        password=settings.proc_scalar_lock_url.password
    )

    queue = IronMQ(
        host=settings.IRON_MQ_HOST,
        project_id=settings.IRON_MQ_PROJECT_ID,
        token=settings.IRON_MQ_TOKEN
    )
    if not active_queues:
        active_queues = {}

    data = {}

    for queuename, procname in PROC_MAP.iteritems():
        details = {}
        try:
            details = queue.getQueueDetails(queuename)
            print(repr(details))
            length = details["size"]
        except (HTTPException, requests.exceptions.HTTPError):
            length = 0

        if not procname in data:
            key = "DISABLE_CELERY_%s" % procname
            lock_type = lock.get(key)
            if not lock_type == 0:
                lock_type = 0
            data[procname] = {'count': length, 'active': 0, 'deploy_lock': lock_type}
        else:
            data[procname]['count'] += length

        if procname in active_queues:
            data[procname]['active'] += active_queues[procname]

    return data


def get_active_queues():
    i = app.control.inspect([x for x in QUEUE_MAP.iterkeys()])
    active = {}
    data = {}
    try:
        active = i.active()
    except (HTTPException, requests.exceptions.HTTPError) as e:
        print("HTTPError:" + e)
    if active:
        for queuename in active.iterkeys():
            length = len(active[queuename])
            if queuename in data:
                data[queuename] += length
            else:
                data[queuename] = length
    return data
