from uuid import UUID,uuid4
from django.db import models
from main.methods import filterNickname
from time import time
from datetime import datetime
from django.utils import timezone
from people.models import Profile,Topic
from projects.models import Tag
from .apps import APPNAME
from django.conf import settings
from main.strings import url
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator


class Article(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    heading = models.CharField(max_length=75)
    subheading = models.CharField(max_length=250)
    author = models.ForeignKey(Profile, related_name = "articles", on_delete=models.CASCADE)
    is_draft = models.BooleanField(default=True)
    nickname = models.CharField(max_length=50,null=True, blank=True)
    preview_image = models.ImageField(null=True, blank=True)
    preview_video = models.FileField(null=True, blank=True)
    createdOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)
    """createdOn (DateTimeField): When the article was created"""
    modifiedOn: datetime = models.DateTimeField(auto_now=False, default=timezone.now)
    admirers = models.ManyToManyField(Profile, through='ArticleAdmirer', default=[
    ], related_name='article_admirers')
    topics = models.ManyToManyField(Topic, through='ArticleTopic', default=[
    ], related_name='article_topics')
    tags = models.ManyToManyField(Tag, through='ArticleTag', default=[
    ], related_name='article_tags')
    raters = models.ManyToManyField(Profile, through="ArticleUserRating", default=[], related_name='article_user_rating')
    """raters (ManyToManyField<Profile>): The raters of the article and their rating"""
    
    def __str__(self):
        return self.nickname if self.nickname else self.id

    def save(self, *args, **kwargs):
        self.modifiedOn = timezone.now()
        super(Article, self).save(*args, **kwargs)
    
    @property
    def CACHE_KEYS(self):
        class CKEYS():
            article_sections = f"article_sections_{self.id}"
            article_admireres = f"article_admirers_{self.id}"
            total_admirers = f"article_total_admirers_{self.id}"
            article_totalratings = f"article_totalratings_{self.id}"
            article_avgratings = f"article_avgratings_{self.id}"
            article_topics = f"article_topics_{self.id}"
            article_tags = f"article_tags_{self.id}"
            article_topics_count = f"article_topics_count_{self.id}"
            article_tags_count = f"article_tags_count_{self.id}"
        return CKEYS()

    @property
    def get_id(self) -> str:
        return self.id.hex
    
    @property
    def get_nickname(self):
        if not self.nickname or self.nickname == str(self.id):
            if self.is_draft:
                if self.nickname:
                    return self.nickname
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

    @classmethod
    def get_cache_one(self, nickname) -> "Article":
        """Returns article instance matching nickname preferably from cache. Returns false if no matching article is found"""
        cacheKey = f"article_{nickname}"
        article = cache.get(cacheKey, None)
        if not article:
            article: Article = Article.objects.filter(nickname=nickname).first()
            if not article:
                return False
            if article.is_draft:
                return article 
            cache.set(cacheKey, article, settings.CACHE_LONG)
        return article

    def getSections(self) -> models.QuerySet:
        """Returns the sections of this article"""
        cacheKey = self.CACHE_KEYS.article_sections
        sections = cache.get(cacheKey, [])
        if not len(sections):
            sections = self.sections.all()
            cache.set(cacheKey, sections, settings.CACHE_LONG)
        return sections

    def get_link(self) -> str:
        """Returns the link to the article"""
        return self.getLink()

    def getLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        """Returns the link to the article"""
        return f"{url.getRoot(APPNAME)}{url.howto.view(self.get_nickname)}{url.getMessageQuery(alert,error,success)}"

    def getEditLink(self, success: str = '', error: str = '', alert: str = '') -> str:
        """Returns the link to the article's edit page"""
        return f"{url.getRoot(APPNAME)}{url.howto.edit(self.get_nickname)}{url.getMessageQuery(alert,error,success)}"

    def get_admirers(self) -> models.QuerySet:
        """Returns the admirers of this article
        """
        cacheKey = self.CACHE_KEYS.article_admireres
        admirers = cache.get(cacheKey, [])
        if not len(admirers):
            admirers = self.admirers.all()
            cache.set(cacheKey, admirers, settings.CACHE_INSTANT)
        return admirers
    
    def isAdmirer(self, profile: Profile) -> bool:
        """Returns True if the profile is an admirer of the article"""
        return self.admirers.filter(id=profile.id).exists()
    
    def total_admirers(self) -> int:
        """Returns the total number of admirers of the article"""
        cacheKey = self.CACHE_KEYS.total_admirers
        count = cache.get(cacheKey, None)
        if not count:
            count = self.admirers.count()
            cache.set(cacheKey, count, settings.CACHE_INSTANT)
        return count

    def getTopics(self) -> list:
        cacheKey = self.CACHE_KEYS.article_topics
        topics = cache.get(cacheKey, None)
        if not topics:
            topics = self.topics.all()
            cache.set(cacheKey, topics, settings.CACHE_INSTANT)
        return topics
    
    def getPalleteTopics(self, limit: int = 2) -> models.QuerySet:
        """Returns the topics of the article to be used in the pallete

        Args:
            limit (int, optional): The limit of topics to be returned. Defaults to 2.

        Returns:
            models.QuerySet<Topic>: The topic instances of the article to be used in the pallete
        """
        return self.getTopics()[:limit]
    
    def getTags(self) -> list:
        cacheKey = self.CACHE_KEYS.article_tags
        tags = cache.get(cacheKey, None)
        if not tags:
            tags = self.tags.all()
            cache.set(cacheKey, tags, settings.CACHE_INSTANT)
        return tags
    
    def getPalleteTags(self, limit: int = 2) -> models.QuerySet:
        """Returns the tags of the article to be used in the pallete

        Args:
            limit (int, optional): The limit of tags to be returned. Defaults to 2.

        Returns:
            models.QuerySet<Tag>: The tag instances of the article to be used in the pallete
        """
        return self.getTags()[:limit]
    
    def isEditable(self) -> bool:
        """Returns whether the article can be edited or not"""
        return self.is_draft or cache.get(f"article_editable_{self.id}", False)
    
    def total_ratings(self):
        """Returns the total numbers of Rating of the article"""
        cacheKey = self.CACHE_KEYS.article_totalratings
        total_ratings = cache.get(cacheKey, None)
        if total_ratings is None:
            total_ratings = ArticleUserRating.objects.filter(article=self).count()
            cache.set(cacheKey, total_ratings, settings.CACHE_INSTANT)
        return total_ratings
    
    def get_rating_out_of_ten(self):
        """Returns the Rating out of 10 of the article"""
        rating_list=ArticleUserRating.objects.filter(article=self)
        num_of_ratings=self.total_ratings()
        total_sum=0
        for rating in rating_list:
            total_sum += rating.score
        return round(total_sum/(num_of_ratings))
    
    def get_avg_rating(self):
        """Returns the average Rating of the article"""
        cacheKey = self.CACHE_KEYS.article_avgratings
        avgrating = cache.get(cacheKey, None)
        if not avgrating:
            rating_list=ArticleUserRating.objects.filter(article=self)
            num_of_ratings=len(rating_list)
            if (num_of_ratings==0):
                return 0.0
            total_sum=0
            for rating in rating_list:
                total_sum += rating.score
            avgrating = round(total_sum/(2*num_of_ratings),1)
            cache.set(cacheKey, avgrating, settings.CACHE_INSTANT)
        return avgrating
    
    def is_rated_by(self, profile):
        """To check whether user has rated or not"""
        return ArticleUserRating.objects.filter(article=self, profile=profile).exists()

    def rating_by_user(self, profile):
        """Returns the Rating of the article by the user"""
        rating = ArticleUserRating.objects.filter(article=self, profile=profile).first()
        if not rating:
            return 0
        return rating.score
    
    def getImage(self):
        """Returns any one section image if exists else returns author's profile picture"""
        return self.preview_image.url if self.preview_image else self.author.get_dp
    
    def getVideo(self):
        """Returns any one section video if exists else returns False"""
        return self.preview_video.url if self.preview_video else False
    
    def totalTopics(self) -> int:
        """Returns the total number of topics of the article"""
        cacheKey = self.CACHE_KEYS.article_topics_count
        count = cache.get(cacheKey, None)
        if count is None:
            count = self.topics.count()
            cache.set(cacheKey, count, settings.CACHE_INSTANT)
        return count
    
    def totalTags(self) -> int:
        """Returns the total number of tags of the article"""
        cacheKey = self.CACHE_KEYS.article_tags_count
        count = cache.get(cacheKey, None)
        if count is None:
            count = self.tags.count()
            cache.set(cacheKey, count, settings.CACHE_INSTANT)
        return count


def sectionMediaPath(instance, filename):
    fileparts = filename.split('.')
    return f"{APPNAME}/sections/{str(instance.get_id)}-{str(uuid4().hex)}.{fileparts[-1]}"


class Section(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    article = models.ForeignKey(Article, related_name = "sections", on_delete=models.CASCADE)
    subheading = models.CharField(max_length=75)
    paragraph = models.CharField(max_length=1200)
    image = models.ImageField(upload_to=sectionMediaPath, null=True, blank=True)
    video = models.FileField(upload_to=sectionMediaPath, null=True, blank=True)

    def __str__(self):
        return self.subheading
        
    def save(self, *args, **kwargs):
        if not self.article.preview_video and self.video:
            self.article.preview_video = self.video
            self.article.save()
        if not self.article.preview_image and self.image:
            self.article.preview_image = self.image
            self.article.save()
        super(Section, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.video and self.article.preview_video==self.video:
            sections = self.article.sections.exclude(video__exact='').exclude(id=self.id)
            if sections:
                self.article.preview_video = sections[0].video
                self.article.save()
            else:
                self.article.preview_video.delete()
        if self.image and self.article.preview_image==self.image:
            sections = self.article.sections.exclude(image__exact='').exclude(id=self.id)
            if sections:
                self.article.preview_image = sections[0].image
                self.article.save()
            else:
                self.article.preview_image.delete()
        return super(Section, self).delete(*args, **kwargs)

    @property
    def get_id(self):
            return self.id.hex
    
    def get_image(self) -> str:
        """Returns the image URL of the section"""
        return f"{settings.MEDIA_URL}{str(self.image)}"

    def get_video(self) -> str:
        """Returns the video URL of the section"""
        return f"{settings.MEDIA_URL}{str(self.video)}"


class ArticleAdmirer(models.Model):
    """Model for relation between an admirer and an article"""
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
    """Model for relation between an admirer and an article"""
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


class ArticleUserRating(models.Model):
    """Model for relation between a rater and an article"""
    class Meta:
        unique_together = ('profile', 'article')

    id: UUID = models.UUIDField(
        primary_key=True, default=uuid4, editable=False)
    profile: Profile = models.ForeignKey(
        Profile, on_delete=models.CASCADE, related_name='article_rater_profile')
    """profile (ForeignKey<Profile>): profile who rated the article"""
    article: Article = models.ForeignKey(
        Article, on_delete=models.CASCADE, related_name='rated_article')
    """article (ForeignKey<Article>): article which was rated"""
    score: float = models.FloatField(default=0, validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    


    
    