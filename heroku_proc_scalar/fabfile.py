from fabric.api import task
from .utils import shutdown_celery_processes, start_dynos


@task
def shutdown_celery_process(*worker_hostnames):

    return shutdown_celery_processes(worker_hostnames)


@task
def shutdown_celery_process_for_deployment():

    return shutdown_celery_processes([], 'deployment')


@task
def restart_processes(*worker_hostnames):

    return start_dynos(worker_hostnames)
