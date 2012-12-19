from fabric.api import task
from .utils import shutdown_celery_processes, start_dynos, get_running_processes
import re


@task
def shutdown_celery_process(*worker_hostnames):

    return shutdown_celery_processes(worker_hostnames)


@task
def shutdown_celery_process_for_deployment():

    return shutdown_celery_processes([], 'deployment')


@task
def restart_processes(*worker_hostnames):

    return start_dynos(worker_hostnames)


@task
def print_running_processes():

    proclist = get_running_processes()
    list = []

    r = re.compile("^(\w+)$", re.M)

    for line in proclist:
        if 'No handlers could be found ' in line:
            continue
        else:
            match = r.finditer(line)
            if match:
                list.append(match[0])
    print ",".join(list)
