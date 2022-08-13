from uuid import UUID,uuid4
from django.db import models
class Article(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True)
    heading = models.CharField(max_length=30)
    subheading = models.CharField(max_length=30)
    is_draft = models.BooleanField(default=True)
    
    def get_url(self)->str:
        url = self.heading.replace(" ","-")
        
        

class Section(models.Model):
    id: UUID = models.UUIDField(
        primary_key=True)
    article = models.ForeignKey(Article,on_delete=models.CASCADE)
    
    