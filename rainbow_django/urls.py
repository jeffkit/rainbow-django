from django.conf.urls import patterns, url

urlpatterns = patterns(
    'rainbow_django.views',
    url(r'^connect/$', 'connect'),
    url(r'^close/$', 'close'),
    url(r'^message/(?P<msg_type>\d+)/$', 'on_message'),
    )
