# -*- coding: utf-8 -*- 
# Create your views here.
from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import ListView, TemplateView
from django.shortcuts import render_to_response
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django import http
from datetime import datetime,timedelta
import httplib
import urllib2
import urllib
import json
import re
import string
import random

import base64
from reader.SubsForm import SubsForm, RegistrationForm, BeforeRegister, LoginForm
import xml.etree.ElementTree as ET
from decorators import json_response
from models import UserSubscribe , UserAttribute, Feed, Story, Folder, RUserStory
from django.views.generic.edit import FormView
from sae.mail import send_mail
from bs4 import BeautifulSoup
import feedparser
from fullrssmaker import upgradeLink
from dateutil import parser
import pytz 
import logging
import socket

logger = logging.getLogger(__name__)
socket.setdefaulttimeout(50)

#from prpcrypt import prpcrypt

# TODO render the page need refine
class HomeView(ListView):
    context_object_name = 'folder_list'
    template_name = 'reader/reader.html'

    def get_queryset(self):
        folders = self.getfolders(self.request.user.id)
        return folders

    def get_context_data(self, **kwargs):
        context = super(HomeView, self).get_context_data(**kwargs)
        uss = UserSubscribe.objects.filter(user_id = self.request.user.id).filter(folder_id = 0)
        feedids = [] 
        for us in uss:
            feedids.append(us.feed_id)             
        feeds = Feed.objects.in_bulk(feedids)
        context['feeds'] = feeds
        #context['stories'] = self.get_random_stories(feeds)
        return context
 
    def get_random_stories(self,feeds):
        feed_ids = []
        for feed in feeds:
            feed_ids.append(feed.id)
        return Story.objects.filter(feed_id__in = feed_ids)

    def getfolders(self,user_id):
        folders_in_db = Folder.objects.filter(user_id = user_id)
        folders = []
        for folder_in_db in  folders_in_db:
            folder = {}
            subs = UserSubscribe.objects.filter(user_id = user_id).filter(folder_id = folder_in_db.id)
            folder['name'] = folder_in_db.name
            folder['id'] = folder_in_db.id
            feedids = []
            for sub in subs:
                feedids.append(sub.feed_id)
            feeds = Feed.objects.in_bulk(feedids) 
            folder['feeds'] = feeds
            folders.append(folder) 
        return folders
    
   


class _RequestPassingFormView(FormView):
    """
    A version of FormView which passes extra arguments to certain
    methods, notably passing the HTTP request nearly everywhere, to
    enable finer-grained processing.
    
    """
    def get(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class(request)
        form = self.get_form(form_class)
        return self.render_to_response(self.get_context_data(form=form))


    def post(self, request, *args, **kwargs):
        # Pass request to get_form_class and get_form for per-request
        # form control.
        form_class = self.get_form_class(request)
        form = self.get_form(form_class)
        if form.is_valid():
           # Pass request to form_valid.
           return self.form_valid(request, form)
        else:
           return self.form_invalid(request, form)

    def get_form_class(self, request=None):
        return super(_RequestPassingFormView, self).get_form_class()

    def get_form_kwargs(self, request=None, form_class=None):
        return super(_RequestPassingFormView, self).get_form_kwargs()

    def get_initial(self, request=None):
        return super(_RequestPassingFormView, self).get_initial()

    def get_success_url(self, request=None, user=None):
        # We need to be able to use the request and the new user when
        # constructing success_url.
        return super(_RequestPassingFormView, self).get_success_url()

    def form_valid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_valid(form)

    def form_invalid(self, form, request=None):
        return super(_RequestPassingFormView, self).form_invalid(form)

class IndexView(TemplateView):

#      success_url='/login/'
      def dispatch(self, request, *args, **kwargs):
          """
          Check that user signup is allowed before even bothering to
          dispatch or do other processing.
        
          """
          if request.user.is_authenticated():
             return redirect('/reader/')
          else:
             return super(IndexView, self).dispatch(request, *args, **kwargs)


class JSONResponseMixin(object):
    def render_to_response(self, context):
        "Returns a JSON response containing 'context' as payload"
        return self.get_json_response(self.convert_context_to_json(context))

    def get_json_response(self, content, **httpresponse_kwargs):
        "Construct an `HttpResponse` object."
        return http.HttpResponse(content,
                                 content_type='application/json',
                                 **httpresponse_kwargs)

    def convert_context_to_json(self, context):
        "Convert the context dictionary into a JSON object"
        # Note: This is *EXTREMELY* naive; in reality, you'll need
        # to do much more complex handling to ensure that arbitrary
        # objects -- such as Django model instances or querysets
        # -- can be serialized as JSON.
        return json.dumps(context)


class LoginView(FormView,JSONResponseMixin):
      form_class = LoginForm
      success_url = '/reader/'
      
      @json_response
      def post(self, request, *args, **kwargs):
          form = LoginForm(request.POST)
          if form.is_valid():
             email = form.cleaned_data['username']
             foundedUser = User.objects.filter(email = email)
             if len(foundedUser) > 0:
                 username = foundedUser[0].username
                 if username is not None: 
                    u = authenticate(username = username,
                                 password = form.cleaned_data['password'])             
                    if u is not None:
                       login(request,u)
                       request.session['userid'] = u.id
                       data = {}
                       data["code"] = "0"
                       return JSONResponseMixin.render_to_response(self,data)
                    else:
                       data = {}
                       data["code"] = "1"
                       return JSONResponseMixin.render_to_response(self,data)
                 else:
                       data = {}
                       data["code"] = "2"
                       return JSONResponseMixin.render_to_response(self,data) 
             else:
                 data = {}
                 data["code"] = "2"
                 return JSONResponseMixin.render_to_response(self,data)               
          else:
             data = {}
             data["code"] = "2"
             return JSONResponseMixin.render_to_response(self,data)               

class BeforeRegistrationView(FormView,JSONResponseMixin):
      form_class=BeforeRegister

      def post(self, request, *args, **kwargs):
          form = BeforeRegister(request.POST)
          if form.is_valid():
             self.send_mail(form)
             data = {}
             data['code'] = '0'
             return JSONResponseMixin.render_to_response(self,data)
          else:
             data = {}
             data["code"] = '1'
             return JSONResponseMixin.render_to_response(self,data)

      def send_mail(self,form):
          receiver = form.cleaned_data['email']
          content = base64.encodestring(receiver)
          str_url = 'http://diggg.sinaapp.com/register?p=' + content
          send_mail(receiver, "invite", str_url,
                    ("smtp.163.com", 25, "diggg_noreply@163.com", "diggg1234", True))          
          
      def form_invalid(self, form):
          return super(BeforeRegistrationView,self).form_invalid(form)





class RegistrationView(_RequestPassingFormView,JSONResponseMixin):
    disallowed_url = 'registration_disallowed'
    form_class = RegistrationForm
    http_method_names = ['get', 'post', 'head', 'options', 'trace']
    success_url = '/reader/'
    template_name = 'reader/register.html'

    def dispatch(self, request, *args, **kwargs):
        """
        Check that user signup is allowed before even bothering to
        dispatch or do other processing.
        
        """
        if not self.registration_allowed(request):
            return redirect(self.disallowed_url)
        return super(RegistrationView, self).dispatch(request, *args, **kwargs)

    def form_invalid(self,request, form):
        data = {}
        data["code"] = "1"
        return JSONResponseMixin.render_to_response(self,data)        

    def form_valid(self, request, form):
        code = self.register(request, **form.cleaned_data)
        data = {}
        data["code"] = code
        return JSONResponseMixin.render_to_response(self,data)
        
    def get_context_data(self, **kwargs):
        context = super(RegistrationView, self).get_context_data(**kwargs)
        mail_str = self.request.GET.get('p')
        if mail_str is not None:
           mail_decode = base64.decodestring(mail_str)
           context['email'] = mail_decode
        return context

    def registration_allowed(self, request):
        return True

    def register(self, request, **cleaned_data):
        checked_username = User.objects.filter(username = cleaned_data['username'])
        if len(checked_username) > 0:
           return '2'
        checked_email = User.objects.filter(email = cleaned_data['email'])
        if len(checked_email) > 0:
           return '1'
        user = User.objects.create_user(username = cleaned_data['username'],
                                        email = cleaned_data['email'], 
                                        password = cleaned_data['password1'])

        u = authenticate(username = cleaned_data['username'],password = cleaned_data['password1'])
        request.session['userid'] = user.id
        login(request,u)
        return '0'

@json_response
def auth(request):
     username = request.GET.get('username')
     id = request.GET.get('id') 
     # find db by username and thirdpaty_id if there is one then login else create one user
     # TODO it's not safe here , because it's not authenticate with the thirdparty feedback code
     # need imporve the authenticate process also need drop the js authenticate
     u = authenticate(username=username,password='111111') 
     if u is not None:
          login(request,u)
          return {'code':'000'}
     else:
          u = User.objects.create_user(username=username)
          u.set_password('111111')
          u.save()
          UserAttribute.objects.create(username = username,thirdparty_id = id,user_id=u.id)
          if u is not None:
             u = authenticate(username=username,password='111111') 
             login(request,u)
             return {'code':'000'}
          else:
             return {'code':'100'}

@json_response
def search_feed(request):
    '''
    search feeds by key word
    '''
    keyword = request.GET.get('keyword')

    p = re.compile('(http://)?((\w)+.)+((com)|(cn)|(org)|(net)){1}(.*)$')
    matched = p.match(keyword)
    if matched:
       return search_rss_url(keyword)
    else:
#       encode_keyword = keyword.decode('utf-8')
       return google_feed_search(keyword,request.session['userid'])


def google_feed_search(keyword,user_id):
    encode_keyword = keyword.encode('utf-8')
    query_args = {'q' :encode_keyword,'v' : '1.0'}    
    encoded_args = urllib.urlencode(query_args)
    url = 'http://ajax.googleapis.com/ajax/services/feed/find?' + encoded_args
    
    #proxy_handler = urllib2.ProxyHandler({'http':'http://172.18.30.87:8087'})
    #opener = urllib2.build_opener(proxy_handler)
    #f = opener.open(url)
    f = urllib2.urlopen(url)
    rslt = f.read()
    rslt = json.loads(rslt)
    entries = rslt['responseData']['entries']
    s_rslt = {}
    rss_list = []           
    feedids = UserSubscribe.objects.filter(user_id=user_id).values('feed_id')    
    id_list = []
    for feedid in feedids:
        id_list.append(feedid['feed_id'])
    id_no_duplicated_list = list(set(id_list))
    urls = list(Feed.objects.filter(id__in = id_no_duplicated_list).values('url'))
    urls_list = []
    for u in urls:
        urls_list.append(u['url'])
    for item in entries:
        entry_set = {}
        url = item['url']
        entry_set['url'] = url
        entry_set['title'] = item['title']
        if url in urls_list:
           entry_set['have_add'] = 'True'
        else:
           entry_set['have_add'] = 'False'
        if len(item['contentSnippet']) > 20:
            #TODO need refine here 
            entry_set['contentSnippet'] = item['contentSnippet'][0:30] + '......'
        else:
            entry_set['contentSnippet'] = item['contentSnippet']
        rss_list.append(entry_set)

    s_rslt['code'] = '0'    
    s_rslt['keyword'] = keyword
    s_rslt['data'] = rss_list
    return s_rslt

def search_rss_url(url):
    doc = urllib2.urlopen(url)
    soup = BeautifulSoup(doc)
    links = soup.find_all(type=re.compile("rss"))
    entry_set = {}
    s_rslt = {}
    rss_list = []
    if len(links)==1:
       entry_set['url']=links[0].get('href')
       entry_set['title'] = ''
       entry_set['contentSnippet'] = ''
       rss_list.append(entry_set)
       s_rslt['code'] = '0'
       s_rslt['data'] = rss_list
       return s_rslt
    else:
       s_rslt['code'] = '1'
       s_rslt['data'] = rss_list
       return s_rslt

@json_response
def subscribe(request):
    feed_key_word = request.GET.get('keyword',None)
    cur_page = request.GET.get('p',None)
    if cur_page is None:
       cur_page = 1
    body = {}
    if feed_key_word is not None:
          feed = ModelFeed()
          msg,feed_id = feed.parse(feed_key_word)
          if feed_id is not None  :
                body['code'] = '0'
                body['data'] = get(cur_page = cur_page,feed_id=feed_id,user_id=request.session['userid'])
                body['feed_id'] = feed_id
                body['feed_title'] = Feed.objects.get(pk=feed_id).title
                us = UserSubscribe.objects.filter(feed_id = feed_id)
                if(len(us) > 0):
                   body['have_add'] = 'True'
                else:
                   body['have_add'] = 'False'
                return body
    else:
       return {'code':'100','msg':'key word is none'}

def outsystem(request):
    logout(request)
    return render_to_response('reader/logout.html')

@json_response
def save_user_subscribe(request):
    if request.user.is_authenticated(): 
       form = SubsForm(request.GET)
       if form.is_valid():
          folder_id = form.cleaned_data['folder_id']
          feed_id = form.cleaned_data['feed_id']
          if folder_id is None:
             folder_id = 0
          uss = UserSubscribe.objects.filter(user_id = request.user.id).filter(feed_id = feed_id)
          if len(uss) <= 0 :
             s = UserSubscribe( user_id = request.user.id,
                                folder_id = folder_id ,
                                feed_id = feed_id )
             s.save()
             feed = Feed.objects.get(pk = feed_id)
             return {'code':'0','title':feed.title,'feed_id':feed.id}
          else:
             return {'code':'100','msg':'user aleardy subscribe','user_id': request.user.id}  
       else:
          return {'code' : '101'}
    else:
       return {'code':'102'}

@json_response
def save_user_searched_feed(request):
    feed_url = request.GET.get('url',None)
    title = request.GET.get('title',None)
    if feed_url is not None and title is not None:
       feeds = Feed.objects.filter(url = feed_url)
       if len(feeds) >= 1 :
          feed = feeds[0]
       else:
          feed = Feed.objects.create(url = feed_url,title = title)
       s = UserSubscribe( user_id = request.user.id,
                          folder_id = 0 ,
                          feed_id = feed.id )
       s.save()       
       return {'code' : '0','feed_id' : feed.id,'title' : title,'feed_url' : feed_url}
    else:
       return {'code' : '1'}          

@json_response
def add_folder(request):
    dir_name = request.GET.get('name')
    folder = Folder.objects.create( name = dir_name,
                           user_id = request.user.id )
    return {'code':'000','folder_id': folder.id} 

@json_response
def dele_folder(request):
    f_id = request.GET.get("fid")
    Folder.objects.filter(id = f_id).delete()
    # TODO delete the subs under the folder id or move the subs out of the folder 
    us = UserSubscribe.objects.filter(folder_id = f_id )
    for u in us:
        u.delete()
    return {'code':'000'}

@json_response
def update_subs_folder(request):
    feed_id = request.GET.get('feedid')
    from_folder_id = request.GET.get('from_folderid')
    to_folder_id = request.GET.get('to_folderid')
    subs = UserSubscribe.objects.filter( feed_id = feed_id,
                                         folder_id = from_folder_id,
                                         user_id = request.user.id 
                                       ).update(folder_id = to_folder_id)
    return {'code' : '000'}

@json_response
def get_stories(request):
    cur_page = request.GET.get('p')
    feed_id = request.GET.get('feedid')
    body = {}
    body['code'] = '000'
    feed = Feed.objects.get(pk=feed_id)
    feedService = ModelFeed()
    msg,feed_id = feedService.parse(feed.url)
    if(feed_id == 0):
       body['code'] = '100'
       return body
    else:
       user_id = request.session['userid']
       data = get(cur_page,feed_id,user_id)
       body['data'] = data
       body['feed_title'] = feed.title
       body['feed_id'] = feed_id
       return body

@json_response
def mark_story_readed(request):
    url = request.GET.get('url')
    fid = request.GET.get('fid')
    body = {}

    decode_url = url.decode('utf-8')
    stories = Story.objects.filter(link = decode_url,feed_id = fid) 
    if len(stories) > 0:
       story = stories[0]
       RUserStory.objects.get_or_create(user_id = request.session['userid'] ,
                                           story_id = story.id)
       body['code'] = '0'
    return body


def get(cur_page,feed_id,user_id):
        offset = 20
        if feed_id is not None:
           if cur_page is not None:
             start_num = (int(cur_page) - 1) * offset  
             end_mum = int(start_num) + offset
             stories = Story.objects.filter(feed_id=feed_id).order_by('-updated')[start_num : end_mum] 
           else : 
             stories = Story.objects.filter(feed_id=feed_id).order_by('-updated')[:offset]         
        else:
           stories = Story.objects.all().order_by('-updated')[:offset]
        stories_set = []
        stories_list = {}
        for story in stories:
            data = {}
            data['url'] = story.link
            data['title'] = story.title
            data['contentSnippet'] = story.summary
            data['id'] = story.id
            data['read'] = "False"
            data['time'] = change_time_format_for_view(story.updated)
            data['author'] = story.author
            stories_set.append(data)
        return filter_user_have_read_stories(stories_set,user_id)

def filter_user_have_read_stories(stories,user_id):
    user_read_stories = RUserStory.objects.filter(user_id = user_id)    
    user_read_stories_ids = []
    for urs in user_read_stories:
        user_read_stories_ids.append(urs.story_id)
    stories_ids = []   
    for story in stories:
        stories_ids.append(story['id'])
    intersection_ids = [val for val in stories_ids if val in user_read_stories_ids]
    for story in stories:    
        if story['id'] in intersection_ids:
           story['read'] =" True"
    return stories

def change_time_format_for_view(updated_time):
    now = datetime.now(pytz.utc)
    delta_time = now - updated_time
    total_seconds = delta_time.total_seconds()
    updated_time = convert_dt_to_aisa_timezone(updated_time)
    if delta_time < timedelta(hours = 12):
       return updated_time.strftime('%H:%M')
    elif delta_time < timedelta(days = 2):
       return 'Yesterday'
    else:
       return updated_time.strftime('%b-%d')

def convert_dt_to_aisa_timezone(time):
    asia_tz = pytz.timezone('Asia/Shanghai')    
    time_str = time.strftime('%Y-%m-%d %H:%m:%S GMT')
#    logger.info('info time string : ' + time_str)
    time = parser.parse(time_str)
    time = time.astimezone(asia_tz)
    return time

class ModelFeed: 

    def __init__(self): 
        self.data = [] 

    def feeddata (self, feedname): 
        feedaddress = feedinfo[feedname] 
        return feedaddress 

    def batchSave(self, stories,pf, feed):
        story_set = []
        for item in stories:
            if hasattr(item,'published'):
               updated = item['published']
            elif hasattr(item,'created'):
               updated = item['created']
            elif hasattr(item,'updated'):
               updated = item['updated']
            elif hasattr(pf,'modified'):
               updated = pf['modified']
            elif hasattr(pf,'published'):
               updated = pf['published']
            if hasattr(item,'summary'):
               summary = item['summary']
            elif hasattr(item,'summary_detail'):
               summary = item['summary_detail']
            else:
               summary = '......'
            story_set.append(Story(link = item['link'],
                                   title = item['title'],
                                   summary = summary,
                                   feed_id = feed.id ,
                                   updated = parser.parse(updated)))                                    
        stories = Story.objects.filter(feed_id = feed.id)
        if(len(stories) <= 0):
           Story.objects.bulk_create(story_set)                         
        else:
           latest_ts = self.get_feed_last_update_time(feed)
           story_set = self.remove_old_entries(story_set,latest_ts)
           Story.objects.bulk_create(story_set)      
           if len(story_set) > 0 :
              feed.updated = self.get_latest_story(story_set).updated
              feed.save()

    def get_feed_last_update_time(self,feed):
        if hasattr(feed,'updated') and feed.updated is not None:
              return feed.updated
        else:
           return parser.parse('1900-10-23 00:00:00')

    def remove_old_entries(self, stories, latest_ts):
        new_stories = []
        for story in stories:
             if self.moreUp2Date(story.updated, latest_ts):
                new_stories.append(story)
        return new_stories

    def get_latest_story(self,stories):
        if len(stories) > 0 :
           latest_story = stories[0]
           for story in stories:
              if self.moreUp2Date(story.updated,latest_story.updated):
                 latest_story = story
           return latest_story

    def moreUp2Date(self,time1,time2):
        fmt = '%a, %d %b %Y %H:%M:%S GMT'
        t1 = convert_dt_to_aisa_timezone(time1)
        t2 = convert_dt_to_aisa_timezone(time2)
#        logger.info('t1 :' + t1.strftime(fmt) + ' and t2 : '+ t2.strftime(fmt))
        rslt = (t1 -t2) > timedelta(seconds = 1)
#        logger.info(' rslt :' + str(rslt))
        return rslt

    def parse (self, address): 
        '''
        parse rss and save to db
        '''
        rss_last_modified = ''
        feeds = Feed.objects.filter(url = address)
        feedid = 0
        if len(feeds) >0 :        # non first time parse this feed
            feed = feeds[0]
            rss_last_modified = feed.updated
            logger.debug('*****begin parse address , non first****')
            pf = feedparser.parse(address,
                                  modified = rss_last_modified)  
            logger.debug('*****finished parse address****')
        else :                    # first time to parse this feed
            logger.debug('*****begin parse address****')
            pf = feedparser.parse(address)
            logger.debug('*****finished parse address****')
            feed = Feed.objects.create(url = address, 
                                       title = pf['channel']['title'])
        if len(pf['entries']) > 0 : 
           self.batchSave(pf['entries'],pf,feed)
        return 'ok',feed.id
     
 

   


        
