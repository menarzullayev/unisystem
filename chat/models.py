# chat/models.py
from django.db import models
from django.conf import settings

class News(models.Model):
    title = models.CharField(max_length=200)
    body = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Message(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    txt = models.TextField()
    resp = models.TextField()
    audio = models.FileField(upload_to='voice/', null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)