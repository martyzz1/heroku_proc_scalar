import re
import settings


class NoQueuesFound(Exception):
    pass


def get_queue_maps_from_procfile():
    queuemaps = {}
    e = re.compile("(\w+):.+(--queues|-Q)\s+(\w[\w,\s]*)")
    c = re.compile("(\w+):.+bin\/celery_shutdown.py")
    f = open(settings.PROCFILE)
    lines = f.readlines()
    f.close()

    got_match = 0
    control_app = ''
    for data in lines:
        if data.startswith('#'):
            continue
        match = e.search(data)
        if match:
            proc = match.group(1)
            queue_str = match.group(3)
            queues = [x.strip() for x in queue_str.split(',')]

            queuemaps[proc] = queues
            got_match = 1
        else:
            cmatch = c.search(data)
            if cmatch:
                proc = cmatch.group(1)
                control_app = proc

    if not got_match:
        raise NoQueuesFound("No queues in your Procfile, please specify them with the --queues or -Q flag")
    return queuemaps, control_app


def get_proc_maps(queue_map):
    proc_map = {}
    for procname in queue_map.iterkeys():
        for queue in queue_map[procname]:
            proc_map[queue] = procname

    return proc_map

QUEUE_MAP, CONTROL_APP = get_queue_maps_from_procfile()
PROC_MAP = get_proc_maps(QUEUE_MAP)
