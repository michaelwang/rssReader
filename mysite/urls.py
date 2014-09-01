from django.conf.urls import patterns, include, url

from reader import views
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
from reader.SubsForm import BeforeRegister 
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    #url(r'^$', views.IndexView.as_view(), name='index'),
    # url(r'^mysite/', include('mysite.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/',        include(admin.site.urls)),
    url(r'^feed/',         views.get_stories),
    url(r'^auth/',         views.auth),
    url(r'^reader/',       views.HomeView.as_view()),
    url(r'^register/',     views.RegistrationView.as_view()),
    url(r'^before_register/', views.BeforeRegistrationView.as_view(
#                                              template_name = 'reader/before_register.html'
                                             )),
    url(r'^subs/',         views.subscribe),
    url(r'^loginBack/',    TemplateView.as_view(template_name = 'reader/loginBack.html')),
    url(r'^login',         views.LoginView.as_view(template_name = 'reader/login.html')),
    url(r'^logout/',       views.outsystem),
    url(r'^saveSubs/',     views.save_user_subscribe),
    url(r'^addfolder/',    views.add_folder),    
    url(r'^delfolder/',    views.dele_folder),
    url(r'^updatefolder/', views.update_subs_folder),
    url(r'^search/', views.search_feed),
    url(r'^saveSearchSubs',views.save_user_searched_feed),
    url(r'^markStory/',    views.mark_story_readed),
    url(r'^$',             views.IndexView.as_view(template_name = 'reader/login.html')),
)
