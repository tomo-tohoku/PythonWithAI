from django.db import models

# Create your models here.
class HtmlFile(models.Model):
    url = models.URLField()
    title = models.CharField(max_length = 512)
    intermediate_file = models.FileField(upload_to = 'html/intermediate/')
    result_file = models.FileField(upload_to = 'html/result/')
    created_at = models.DateTimeField(auto_now_add = True)

    def __str__(self):
        return f'id: {self.id}, url: {self.url}, title: {self.title}'
    
    def delete(self, *args, **kwargs):
        # ファイルが存在すれば削除
        if self.intermediate_file:
            self.intermediate_file.delete(save = False)
        
        # ファイルが存在すれば削除
        if self.result_file:
            self.result_file.delete(save = False)
        
        # モデルを削除する
        super().delete(*args, **kwargs)