from fabric.api import task
from .utils import shutdown_celery_processes, start_dynos, get_running_processes


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
    list = ''
    for line in proclist:
        if 'No handlers could be found ' in line:
            continue
        elif len(line) <= 0:
            continue
        else:
            list += ",{0}".format(list)
    print list
