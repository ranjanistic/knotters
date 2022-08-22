from uuid import UUID,uuid4
from django.db import models
from main.methods import filterNickname
from time import time
from datetime import datetime
from django.utils import timezone
from people.models import Profile,Topic
from projects.models import Tag


class Article(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    heading = models.CharField(max_length=100)
    subheading = models.CharField(max_length=200)
    author = models.ForeignKey(Profile, on_delete=models.CASCADE)
    is_draft = models.BooleanField(default=True)
    nickname = models.CharField(max_length=50,null=True, blank=True)
    createdOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the competition was created"""
    modifiedOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)
    admirers = models.ManyToManyField(Profile, through='ArticleAdmirer', default=[
    ], related_name='article_admirers')
    topics = models.ManyToManyField(Topic, through='ArticleTopic', default=[
    ], related_name='article_topics')
    tags = models.ManyToManyField(Tag, through='ArticleTag', default=[
    ], related_name='article_tags')
    
    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        if not self.nickname:
            self.get_nickname()
        super(Article, self).save(*args, **kwargs)
    
    def get_nickname(self):
        if not self.nickname:
            if self.is_draft:
                nickname = self.id
            else:
                nickname = filterNickname(self.heading, 25)
            if Article.objects.filter(nickname__iexact=nickname).exclude(id=self.id).exists():
                nickname = nickname[:12]
                currTime = int(time())
                nickname = nickname + str(currTime)
                while Article.objects.filter(nickname__iexact=nickname).exclude(id=self.id).exists():
                    nickname = nickname[:12]
                    currTime += 200
                    nickname = nickname + str(currTime)
            self.nickname = nickname
            self.save()
        return self.nickname
    
    def get_url(self)->str:
        url = self.getnickname.replace(" ","-")
        self.get_nickname()
        

class Section(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    article = models.ForeignKey(Article,on_delete=models.CASCADE)
    subheading = models.CharField(max_length=100)
    paragraph = models.CharField(max_length=300)
    img = models.ImageField(upload_to='images_uploaded',null=True)
    video = models.FileField(upload_to='videos_uploaded',null=True)
    # validators=[FileExtensionValidator(allowed_extensions=['MOV','avi','mp4','webm','mkv'])])
    delete: Article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='article_section_delet')

    
class ArticleAdmirer(models.Model):
    """Model for relation between an admirer and a project"""
    class Meta:
        unique_together = ('profile', 'article')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='article_admirer_profile')
    """profile (ForeignKey<Profile>): profile who admired the article"""
    article:Article  = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='admired_article')
    """article (ForeignKey<Article>): article which was admired"""

class ArticleTopic(models.Model):
    """Model for relation between an admirer and a project"""
    class Meta:
        unique_together = ('topic', 'article')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    topic: Topic = models.ForeignKey(
        Topic, on_delete=models.CASCADE, related_name='article_topic')
    """topic (ForeignKey<Topic>): topic related to the article"""
    article:Article  = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='topic_article')
    """article (ForeignKey<Article>): article related to topic"""
    
class ArticleTag(models.Model):
    """Model for relation between a tag and an article"""
    class Meta:
        unique_together = ('tag', 'article')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    tag: Tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name='article_tag')
    """tag (ForeignKey<Tag>): tag related to the article"""
    article:Article  = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='tag_article')
    """article (ForeignKey<Article>): article related to tag"""


    
    