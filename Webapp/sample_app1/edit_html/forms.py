from django import forms

class EditForm(forms.Form):
    url = forms.URLField(label = 'URL', required = True, \
        widget = forms.URLInput(attrs = {'class': 'form-control'}))
    style_area = forms.CharField(label = '挿入する <style>タグの中身を入力してください', required = False, \
        widget = forms.Textarea(attrs = {'placeholder': 'body {background-color: skyblue;}'}))