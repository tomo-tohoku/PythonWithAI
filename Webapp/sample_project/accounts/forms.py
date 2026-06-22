from django import forms

class LoginForm(forms.Form):
    username = forms.CharField(
        label = "ユーザ名",
        widget = forms.TextInput(attrs = {"class": "form-control"})
    )
    password = forms.CharField(
        label = "パスワード",
        widget = forms.PasswordInput(attrs = {"class": "form-control"}),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label_suffix = "" # ラベルのコロンを消す