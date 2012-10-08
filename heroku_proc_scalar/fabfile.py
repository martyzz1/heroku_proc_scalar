from fabric.api import task
from . import shutdown_celery_processes


@task
def shutdown_celery_process(*worker_hostnames):

    shutdown_celery_processes(worker_hostnames)


@task
def shutdown_celery_process_for_deployment():

    shutdown_celery_processes([], 'deployment')
