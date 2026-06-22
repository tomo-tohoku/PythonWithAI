from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm

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