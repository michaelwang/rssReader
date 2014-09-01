"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.test import Client
from reader.models import UserSubscribe,Story,Folder,Feed,RUserStory
from reader.views import ModelFeed, UserAttribute
import json
import feedparser
from django.contrib.auth.models import User 

class ReaderRss(TestCase):

    def prelogin(self):
        '''
        this is help method  for tests which need login the system
        '''
        u = User.objects.create_user('name','name@test.com','111111')
        c = Client()
        iflogin = c.login(username='name',password='111111')
        self.assertEqual(True,iflogin)
        return c,u.id

    def test_keyword(self):
        """
         Test wether input keyword is url 
        """
        c = Client()
        response = c.get('/subs/',{'keyword':'aaaa'})
        result = json.loads(response.content)
        self.assertEqual(result["code"],"100")

    def test_auth(self):
        c = Client()
        c.get('/auth/',{'username':'testusername' ,
                        'id' : 12} )
        u = User.objects.filter(username = 'testusername')       
        if u is None:
           self.assertFalse(True)
        ua = UserAttribute.objects.filter(user_id = u[0].id) 
        if ua is None:
           self.assertFalse(True) 

    def test_user_subs(self):
        """
         Test user add subscribe site  
        """             
        before_add = UserSubscribe.objects.count()
        f = Feed.objects.create(title = 'test feed',
                                url = 'aa.test.com')
        c,uid = self.prelogin()
        response = c.get('/saveSubs/', {'feed_id':f.id})
        self.assertEqual(before_add + 1, UserSubscribe.objects.count())

    def test_parse(self):
        m = ModelFeed()
        feedurl = 'http://news.163.com/special/00011K6L/rss_newstop.xml'        
        name,feed_id = m.parse(feedurl)
        story_size_in_db = len(Story.objects.filter(feed_id=feed_id))
        parse_size =len(feedparser.parse(feedurl)['items'])
        self.assertEqual(story_size_in_db,parse_size)
        #second parse the same rss url
        m.parse(feedurl)
        self.assertEqual(story_size_in_db,parse_size)

    def test_subs(self):
        feedurl = 'http://news.163.com/special/00011K6L/rss_newstop.xml'        
        c = Client()
        r = c.get('/subs/',{'keyword':feedurl})
        db_stories_cnt = Story.objects.count() 
        rslt = json.loads(r.content)
        # print rslt
        self.assertEqual(rslt['code'],'0')
        self.assertIsNotNone(rslt['feed_id']) 

    def test_add_folder(self):
        c,uid = self.prelogin()
        folder_cnt = Folder.objects.count()
        r = c.get('/addfolder/',{'name':'testfolder'})
        rs_json = json.loads(r.content)
        self.assertEqual(rs_json['code'],'000')

    def test_update_folder(self):
        c,uid = self.prelogin()
        feed = Feed.objects.create(url = 'test.aa.com') 
        f  = Folder.objects.create(name = 'testfolder',user_id = uid)
        f2 = Folder.objects.create(name = 'testfolder2',user_id = uid)
        UserSubscribe.objects.create(  folder_id = f.id,
                                       user_id = uid,
                                       feed_id = feed.id) 

        r = c.get('/updatefolder/',{'feedid':feed.id,
                                'from_folderid':f.id,
                                'to_folderid':f2.id    
                               })
        rs_json = json.loads(r.content)
        self.assertEqual(rs_json['code'],'000')        
        usubs = UserSubscribe.objects.filter(user_id = uid,feed_id = feed.id)
        self.assertEqual(usubs[0].folder_id,f2.id)

    def test_del_folder(self):
        c,uid = self.prelogin()
        feed = Feed.objects.create(url = 'test.aa.com') 
        
        f = Folder.objects.create(name = 'testfolder',user_id = uid)
        UserSubscribe.objects.create(  folder_id = f.id,
                                       user_id = uid,
                                       feed_id = feed.id) 
        before_delete_feed_size = Feed.objects.filter(url = 'test.aa.com').count()
        before_delete_folder_size = Folder.objects.filter(name = 'testfolder').count()
        before_delete_subs_size = UserSubscribe.objects.filter(user_id = uid).count()

        r = c.get('/delfolder/',{'fid': f.id}) 

        rs_json = json.loads(r.content)
        self.assertEqual(rs_json['code'],'000')
        self.assertEqual(Feed.objects.count(),before_delete_feed_size)
        self.assertEqual(before_delete_folder_size - 1,Folder.objects.count())
        self.assertEqual(before_delete_subs_size - 1,UserSubscribe.objects.count())

    def test_search_rss_url(self):
        from reader import views
        url = 'http://www.reddit.com/r/Python/'
        rss_url = views.search_rss_url(url)     
        self.assertEqual(rss_url['code'],'0')
        self.assertEqual(rss_url['data'][0]['url'],'http://www.reddit.com/r/Python/.rss')
        url = 'http://news.163.com'
        rss_url = views.search_rss_url(url)
        self.assertEqual(rss_url['code'], '1')
   
    def test_filter_user_have_read_stories(self):
        from reader import views
        stories = []
        for cnt in range(20):
            data = {}
            data['id'] = cnt
            stories.append(data)
        RUserStory.objects.create(user_id = 1,story_id = 1)
        RUserStory.objects.create(user_id = 1,story_id = 2)
        s = views.filter_user_have_read_stories(stories,1)
        print s

    def test_save_search_feed(self):
        c,uid = self.prelogin()
        url = 'www.test.com'
        title = 'test_title'
        r = c.get('/saveSearchSubs/',{'url':url,'title':title})        
        rs_json = json.loads(r.content)
        self.assertEqual(rs_json['code'],'0')
        feed = Feed.objects.filter(url = url)
        self.assertEqual(feed[0].title,title)        

        us = UserSubscribe.objects.filter(user_id = uid)
        self.assertEqual(us[0].feed_id,feed[0].id)

        
        

    def test_search_feed(self):
        c,uid = self.prelogin()
        r = c.get('/search/',{'keyword':'java'})                        
        print r
#        r_json = json.loads(r.content)
#        self.assertEqual(r_json['code'],'0')        



