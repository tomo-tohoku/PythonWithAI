from django.db import models
from django.contrib.auth.models import AbstractUser # カスタムユーザモデル

# Create your models here.
# AbstractUser に元からある項目
# id　ユーザID
# username　ログイン名
# password　ハッシュ化されたパスワード
# email　メールアドレス
# first_name　名
# last_name　姓
# is_active　有効ユーザか
# is_staff　管理画面へ入れるか
# is_superuser　全権限を持つか
# date_joined　登録日時
# last_login　最終ログイン日時
class CustomUser(AbstractUser):
    pass