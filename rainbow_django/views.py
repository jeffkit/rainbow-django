#encoding=utf-8
from django.views.decorators.csrf import csrf_exempt
from rainbow_django import get_handler, get_setting, RAINBOW_TOKEN, \
    RAINBOW_DATA_FORMAT, RainbowRequest, RainbowResponse, \
    RAINBOW_CLIENT_COOKIE, RAINBOW_CLIENT_CHANNEL_SUB, \
    RAINBOW_CLIENT_CHANNEL_UNSUB, RAINBOW_INVALID_REQUEST_REASON, \
    RAINBOW_CLIENT_IDENTITY
from hashlib import sha1
import logging
import json
import base64
log = logging.getLogger(__name__)

from django.http import HttpResponse


def is_valid_request(timestamp, nonce, signature):
    if not (timestamp and nonce and signature):
        return False
    token = get_setting(RAINBOW_TOKEN)
    sign_ele = [token, str(timestamp), str(nonce)]
    sign_ele.sort()
    sign = sha1(''.join(sign_ele)).hexdigest()
    return sign == signature


def rainbow_handler_internal(func):

    def wrapper_func(request, *args, **kwargs):
        # check the signature.
        timestamp = request.GET.get('timestamp', '')
        nonce = request.GET.get('nonce', '')
        signature = request.GET.get('signature', '')

        if not is_valid_request(timestamp, nonce, signature):
            rsp = HttpResponse('')
            rsp[RAINBOW_INVALID_REQUEST_REASON] = 'invalid signature'
            return rsp

        try:
            identity = request.META.get(RAINBOW_CLIENT_IDENTITY, None)
            if not identity:
                rsp = HttpResponse('')
                rsp[RAINBOW_INVALID_REQUEST_REASON] = 'identity is required'
                return rsp
            request.rbidentity = identity
        except:
            print 'error'
            log.error('get identity error', exc_info=True)

        rsp = func(request, *args, **kwargs)

        if isinstance(rsp, HttpResponse):
            return rsp
        if not isinstance(rsp, RainbowResponse):
            return HttpResponse("%s" % rsp)

        # set header & cookies
        try:
            content = rsp.data
            if get_setting(RAINBOW_DATA_FORMAT) == 'json':
                content = json.dumps(content)
            http_rsp = HttpResponse(content)
            if rsp.context:
                print 'contect would be save to header %s' % rsp.context
                http_rsp[RAINBOW_CLIENT_COOKIE] = base64.b64encode(
                    json.dumps(rsp.context))

            if rsp.subscribes:
                http_rsp[RAINBOW_CLIENT_CHANNEL_SUB] = ';;'.join(rsp.subscribes)

            if rsp.unsubscribes:
                http_rsp[RAINBOW_CLIENT_CHANNEL_UNSUB] = ';;'.join(
                    rsp.unsubscribes)
            return http_rsp
        except:
            log.error('rainbow handler error', exc_info=True)

    return wrapper_func


@rainbow_handler_internal
def connect(request):
    """A client connected to rainbow.
    """
    cnt_handler = get_handler('connect')
    if cnt_handler:
        return cnt_handler(request)
    else:
        return HttpResponse(json.dumps({'status': 'success'}))


@rainbow_handler_internal
def close(request):
    """A client connection is closing.
    """
    cl_handler = get_handler('close')
    if cl_handler:
        return cl_handler(request)
    else:
        return HttpResponse(json.dumps({'status': 'success'}))


@csrf_exempt
@rainbow_handler_internal
def on_message(request, msg_type):
    """Receive message from client, just forward.
    """
    try:
        if request.method != 'POST':
            rsp = HttpResponse('')
            rsp[RAINBOW_INVALID_REQUEST_REASON] = 'POST method is required'
            return rsp
        handler = get_handler(int(msg_type))
        data = request.body
        log.info('post data: %s' % data)
        if get_setting(RAINBOW_DATA_FORMAT) == 'json':
            data = json.loads(data)
        context = request.META.get('HTTP_' + RAINBOW_CLIENT_COOKIE, '')
        print 'context %s' % context
        if context:
            context = json.loads(base64.b64decode(context))
        else:
            context = {}
        
        rb_request = RainbowRequest(request.rbidentity, msg_type,
                                    data=data, context=context)
        return handler(rb_request)
    except:
        log.error('handle message error', exc_info=True)
