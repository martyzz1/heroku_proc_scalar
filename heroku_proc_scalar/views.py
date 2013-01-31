from django.http import HttpResponse
from pprint import pprint
import django.utils.simplejson as json
from .utils import get_redis_queue_count, get_active_queues, get_ironmq_queue_count


def redis_queue_count(request):

    active_queues = get_active_queues()
    #print "Active queues\n"
    #pprint(active_queues)
    data = get_redis_queue_count(active_queues)
    #print "data\n"
    #pprint(data)
    return HttpResponse(json.dumps(data), mimetype='application/json')


def ironmq_queue_count(request):

    active_queues = get_active_queues()
    #print "Active queues\n"
    #pprint(active_queues)
    data = get_ironmq_queue_count(active_queues)
    #print "data\n"
    #pprint(data)
    return HttpResponse(json.dumps(data), mimetype='application/json')
