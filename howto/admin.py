from django.contrib import admin 
from howto.models import Article, Section, ArticleAdmirer, ArticleTag, ArticleTopic


admin.site.register(Article)
admin.site.register(Section)
admin.site.register(ArticleTopic)
admin.site.register(ArticleTag)
admin.site.register(ArticleAdmirer)

