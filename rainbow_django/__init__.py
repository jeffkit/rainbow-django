#encoding=utf-8
import warnings
import random
from hashlib import sha1
import time
import requests
import json
import logging
log = logging.getLogger(__name__)


VERSION = 0.1
handler_map = {}
rainbow_settings = {}

### SETTING NAMES ###

RAINBOW_SERVER_URL = 'RAINBOW_SERVER_URL'
RAINBOW_TOKEN = 'RAINBOW_TOKEN'
RAINBOW_DATA_FORMAT = 'RAINBOW_DATA_FORMAT'
RAINBOW_CLIENT_COOKIE = 'RAINBOWCLIENTCOOKIE'
RAINBOW_CLIENT_CHANNEL_SUB = 'RAINBOWCLIENTCHANNEL'
RAINBOW_CLIENT_CHANNEL_UNSUB = 'RAINBOWCLIENTCHANNELUNSUB'
RAINBOW_INVALID_REQUEST_REASON = 'RAINBOWREQUESTINVALID'
RAINBOW_CLIENT_IDENTITY = 'HTTP_RAINBOWCLIENTIDENTITY'

# util methods


def get_setting(name):
    if name in rainbow_settings:
        return rainbow_settings[name]
    from django.conf import settings
    value = getattr(settings, name, '')
    if value:
        rainbow_settings[name] = value
        return value


def signature(token=None):
    ts = int(time.time())
    noce = random.randint(1000, 9999)
    token = get_setting(RAINBOW_TOKEN)
    sign_ele = [token, str(ts), str(noce)]
    sign_ele.sort()
    sign = sha1(''.join(sign_ele)).hexdigest()
    return {'timestamp': ts, 'nonce': noce, 'signature': sign}


def discover_ranibow_handler():
    from django.conf import settings

    for app in settings.INSTALLED_APPS:
        try:
            __import__(app + '.rainbow')
        except:
            pass


def get_handler(name):
    if not handler_map:
        discover_ranibow_handler()
    return handler_map.get(name, None)


# decorators

def rainbow(msg_type):
    """Use this decorator to claim I'm a rainbow handler.
    Rainbow handler is a function which accept a rainbowrequest obj.

    @rainbow(1001)
    def my_handler(rbrequest):
       # do something.
    """

    def decorated(func):
        if msg_type in handler_map and handler_map[msg_type] != func:
            warnings.warn('different function share the same msg_type',
                          RuntimeWarning)

        handler_map[msg_type] = func

        return func
    return decorated


def rainbow_connect(func):
    handler_map['connect'] = func
    return func


def rainbow_close(func):
    handler_map['close'] = func
    return func


class RainbowRequest(object):

    def __init__(self, identity, msg_type, data=None, context=None):
        self.identity = identity
        self.msg_type = msg_type
        self.data = data
        self.context = context


class RainbowResponse(object):

    def __init__(self, data, request=None, context=None):
        self.data = data
        if context:
            self._context = context
        elif request:
            self._context = request.context
        else:
            self._context = None
        self._subsribe = []
        self._unsub = []

    @property
    def context(self):
        if not self._context:
            self._context = {}
        return self._context

    @property
    def subscribes(self):
        if not self._subsribe:
            self._subsribe = []
        else:
            if not isinstance(self._subsribe, (list, tuple)):
                self._subsribe = [self._subsribe]
        return self._subsribe

    @property
    def unsubscribes(self):
        if not self._unsub:
            self._unsub = []
        else:
            if not isinstance(self.unsub, (list, tuple)):
                self._unsub = [self._unsub]
        return self._unsub

    def sub(self, channel):
        self.subscribes.append(channel)

    def unsub(self, channel):
        self.unsubscribes.append(channel)


def send(channel, msg_type, data, qos=0, timeout=10, ignore_result=True):
    """send message to rainbow server, take care of the signature.
    """
    content = json.dumps(data)

    params = {
        'msgtype': msg_type,
        'channel': channel,
        'qos': qos,
        'timeout': timeout,
    }
    params.update(signature())
    connections = None
    status = None
    msg = None
    try:
        result = requests.post(
            get_setting(RAINBOW_SERVER_URL) + '/send/', params=params,
            data=content, timeout=timeout + 0.5)
        log.info('rainbow response=%s', result)
        result = result.json()
        connections = result.get('connections', None)
        status = result.get('status', None)
        msg = result.get('msg', None)
        log.info(
            'send to rainbow, connections=%s, status=%s, msg=%s',
            connections, status, msg)
    except:
        log.error('send back to rainbow error', exc_info=True)

    return connections, status, msg


def subscribe(channel, client, cancel=False):
    """ subscribe client to channel
    """
    data = {'identity': client, 'channel': channel}
    data = json.dumps(data)
    url = get_setting(RAINBOW_SERVER_URL) + '/sub/'
    if cancel:
        url = get_setting(RAINBOW_SERVER_URL) + '/unsub/'
    try:
        log.info('sub_RB request=%s', data)
        result = requests.post(url, data=data, params=signature(), timeout=2)
        result = result.json()
        log.info('sub_RB response=%s', result)
    except:
        log.error('sub_RB error', exc_info=True)


def unsubscribe(channel, client):
    return subscribe(channel, client, True)
