from django.conf.urls import patterns,url

from reader.views import home 
from reader import views 


urlpatterns = patterns('',

    url(r'^$',home, name='index'),
    url(r'^',home, name='index'),
)
