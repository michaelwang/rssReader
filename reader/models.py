from django.db import models

class UserSubscribe(models.Model):
      user_id = models.IntegerField()
      feed_id = models.IntegerField() 
      folder_id = models.IntegerField()

class UserAttribute(models.Model):
      username = models.CharField(max_length=100)
      email = models.CharField(max_length=100)
      city = models.CharField(max_length=20)      
      thirdparty_id = models.CharField(max_length=100)
      user_id = models.IntegerField()

class Feed(models.Model):
      url = models.CharField(max_length=300) 
      title = models.CharField(max_length=300)
      updated = models.DateTimeField(null=True)
      image = models.CharField(max_length=100,null=True)

class Story(models.Model):
      feed_id = models.IntegerField()
      title = models.CharField(max_length=500)
      link = models.CharField(max_length=300)
      updated = models.DateTimeField(null=True)
      author = models.CharField(max_length=100)
      summary = models.TextField()
      media_content = models.CharField(max_length=300)
      content = models.TextField()

class Folder(models.Model):
      name = models.CharField(max_length=200)
      user_id = models.IntegerField()

class RUserStory(models.Model):
      user_id = models.IntegerField()
      story_id = models.IntegerField()
      index_together = ['user_id','story_id']

