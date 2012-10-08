from django.conf.urls import patterns, url

urlpatterns = patterns('heroku_proc_scalar.views',
    url(r'^heroku_proc_scalar/proc_count$', 'redis_queue_count', name='redis_queue_count'),
)
