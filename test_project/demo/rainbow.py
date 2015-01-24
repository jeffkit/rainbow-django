#encoding=utf-8
from rainbow_django import rainbow, rainbow_connect, rainbow_close, \
    RainbowResponse, send, subscribe


@rainbow_connect
def connect(request):
    return RainbowResponse({'status': 'success'})


@rainbow_close
def close(request):
    return RainbowResponse({'status': 'success'})


@rainbow(msg_type=0)
def update_name(rbrequest):
    name = rbrequest.data['message']
    rsp = RainbowResponse({'status': 'ok', 'identity': rbrequest.identity},
                           rbrequest)
    subscribe('room', rbrequest.identity)
    rsp.context['user'] = name

    send('room', 1001, {'name': name, 'identity': rbrequest.identity})
    return rsp


@rainbow(msg_type=1)
def send_message(rbrequest):
    msg = rbrequest.data['message']
    send('room', 1002, {'name': rbrequest.context['user'],
                        'message': msg,
                        'identity': rbrequest.identity})
    return RainbowResponse({'status': 'ok'}, rbrequest)
