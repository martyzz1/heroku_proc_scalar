from fabric.api import task, local, env


@task
def lock_remote_celery_for_deployment():
    cmd = "heroku run fab lock_celery_for_deployment --app %s" % env.app_name
    local(cmd)


@task
def unlock_remote_celery_after_deployment():
    cmd = "heroku run fab unlock_celery_after_deployment --app %s" % env.app_name
    local(cmd)


@task
def shutdown_remote_celery():
    cmd = "heroku run fab shutdown_celery_process_for_deployment --app %s" % env.app_name
    local(cmd)


@task
def get_remote_running_processes():
    cmd = "heroku run fab print_running_processes --app %s" % env.app_name
    result = local(cmd, capture=True)
    if result.failed:
        print result.stderr
        print result.stdout
        print result

    print result
    lines = result.splitlines()
    procline = ''
    for line in lines:
        if line.startswith('PROCLIST='):
            procline = line[9:]

    if not len(procline) > 0:
        print "No processes Running"

    return procline


@task
def restart_remote_processes(proclist_str):
    cmd = "heroku run fab restart_processes_after_deployment:%s --app %s" % (proclist_str, env.app_name)
    local(cmd)
