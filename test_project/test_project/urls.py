from django.conf.urls import patterns, include, url
from django.contrib import admin
import rainbow_django

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'test_project.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^rainbow/', include('rainbow_django.urls')),
    url(r'^chat/$', 'demo.views.chat')
)
