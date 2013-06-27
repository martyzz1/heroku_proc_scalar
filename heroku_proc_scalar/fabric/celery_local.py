from fabric.api import task, local, env


@task
def lock_remote_for_deployment():
    cmd = "heroku run fab celery.lock_for_deployment --app %s" % env.app_name
    local(cmd)


@task
def unlock_remote_after_deployment():
    cmd = "heroku run fab celery.unlock_after_deployment --app %s" % env.app_name
    local(cmd)


@task
def shutdown_remote():
    cmd = "heroku run fab celery.shutdown_process_for_deployment --app %s" % env.app_name
    local(cmd)


@task
def get_remote_running_processes():
    cmd = "heroku run fab celery.print_running_processes --app %s" % env.app_name
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
    cmd = "heroku run fab celery.restart_processes_after_deployment:%s --app %s" % (proclist_str, env.app_name)
    local(cmd)
