from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, RegisterForm
from django.contrib.auth import get_user_model
from django.contrib import messages

User = get_user_model() # CustomUser を使っている

# Create your views here.
def login_view(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            # 認証処理の部分
            # データベースと一致するかどうか確かめる
            user = authenticate(
                request,
                username = username,
                password = password
            )

            if user is not None:
                login(request, user) # request.session にログイン情報が保存される
                return redirect("/edit_html")
            
            form.add_error(
                None,
                "ユーザ名またはパスワードが違います"
            )
    else:
        form = LoginForm()
    
    return render(request, "accounts/login.html", {"form": form})

def logout_view(request):
    logout(request)

    return redirect("login")

def register_view(request):

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():

            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]
            password_confirm = form.cleaned_data["password_confirm"]

            # パスワード一致チェック
            if password != password_confirm:
                form.add_error("password_confirm", "パスワードが一致しません")
                return render(request, "accounts/register.html", {"form": form})

            # ユーザー作成
            # User.objects.create は使わない
            user = User.objects.create_user(
                username = username,
                password = password
            )

            messages.success(request, "ユーザ登録が完了しました")

            return redirect("login")

    else:
        form = RegisterForm()

    return render(request, "accounts/register.html", {"form": form})