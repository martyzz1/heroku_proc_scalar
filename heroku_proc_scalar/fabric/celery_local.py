from fabric.api import task, env


@task
def lock_remote_for_deployment():
    cmd = "fab celery.lock_for_deployment"
    env.app.run_command(cmd)


@task
def unlock_remote_after_deployment():
    cmd = "fab celery.unlock_after_deployment"
    env.app.run_command(cmd)


@task
def shutdown_remote():
    cmd = "fab celery.shutdown_process_for_deployment"
    env.app.run_command(cmd)


@task
def get_remote_running_processes():
    cmd = "fab celery.print_running_processes"
    result, dyno = env.app.run_command(cmd)

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
    cmd = "fab celery.restart_processes_after_deployment:%s" % proclist_str
    env.app.run_command(cmd)
