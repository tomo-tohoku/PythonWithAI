from django.db import models

# Create your models here.
class HtmlFile(models.Model):
    url = models.URLField()
    title = models.CharField(max_length = 100)
    intermediate_file = models.FileField(upload_to = 'html/intermediate/')
    result_file = models.FileField(upload_to = 'html/result/')
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'url: {self.url}, title: {self.title}'