#from pprint import pprint
import re
import os

PROCFILE = os.environ.get('PROCFILE', './Procfile')


class NoQueuesFound(Exception):
    pass


def get_queue_maps():

    queuemaps = {}
    e = re.compile("(\w+):.+(--queues|-Q)\s+(\w[\w,\s]*)")
    c = re.compile("(\w+):.+bin\/celery_shutdown.py")
    print "reading procfile %s" %PROCFILE
    f = open(PROCFILE)
    lines = f.readlines()
    f.close()
    got_match = 0
    control_app = ''
    for data in lines:
        #print data
        match = e.search(data)
        if match:
            proc = match.group(1)
            queue_str = match.group(3)

            #print "%s => %s" % (proc, queue_str)

            #queues = queue_str.replace(' ', '').split(',')
            queues = [x.strip() for x in queue_str.split(',')]

            queuemaps[proc] = queues
            got_match = 1
        else:
            cmatch = c.search(data)
            if cmatch:
                proc = cmatch.group(1)
                control_app = proc

    if not got_match:
        raise NoQueuesFound("No queues are specified in your Procfile, please specify them with the --queues or -Q flag")
    #pprint(queuemaps)
    return queuemaps, control_app


def get_proc_maps(queue_map):
    #dsd
    proc_map = {}

    for procname in queue_map.iterkeys():
        for queue in queue_map[procname]:
            proc_map[queue] = procname

    return proc_map

QUEUE_MAP, CONTROL_APP = get_queue_maps()
PROC_MAP = get_proc_maps(QUEUE_MAP)

#pprint(PROC_MAP)
