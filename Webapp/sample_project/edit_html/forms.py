from django import forms

class EditForm(forms.Form):
    url = forms.URLField(label = 'URL', required = True, \
        widget = forms.URLInput(attrs = {'class': 'form-control'}))
    style_area = forms.CharField(label = '挿入する <style>タグの中身を入力してください', required = False, \
        widget = forms.Textarea(
            attrs = {
                'placeholder': '例）body {background-color: skyblue;}',
                'class': 'form-control'
                }
            )
        )

class ArrangeForm(forms.Form):
    tag = forms.CharField(label = "タグの選択", required = False, \
        widget = forms.TextInput(attrs = {'class': 'form-control'}))
    selected_class = forms.CharField(label = "クラスの選択", required = False, \
        widget = forms.TextInput(attrs = {'class': 'form-control'}))
    selected_id = forms.CharField(label = "ＩＤの選択", required = False, \
        widget = forms.TextInput(attrs = {'class': 'form-control'}))
    style_area = forms.CharField(label = '挿入する style 属性の中身を入力してください', required = True, \
        widget = forms.Textarea(
            attrs = {
                'placeholder': '例）background-color: skyblue;',
                'class': 'form-control'
                }
            )
        )