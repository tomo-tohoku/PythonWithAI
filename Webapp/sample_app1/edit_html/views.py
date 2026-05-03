from django.shortcuts import render, redirect
from .forms import EditForm
from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright
import time
import os
from pathlib import Path

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INTERMEDIATE_FILE_PATH = os.path.join(BASE_DIR, "templates/edit_html/intermediate.html")
RESULT_FILE_PATH = os.path.join(BASE_DIR, "templates/edit_html/result.html")
FILE_PATH_OBJ = Path(RESULT_FILE_PATH)

# Create your views here.
def index(request):
    if request.method == "GET":
        params = {
            'error_msg': '',
            'edit_form': EditForm()
        }
        return render(request, 'edit_html/index.html', params)

def result(request):
    if request.method == "GET":
        if FILE_PATH_OBJ.exists() == True and FILE_PATH_OBJ.is_file() == True:
            params = {
                'error_msg': '',
                'edit_form': EditForm()
            }
            return render(request, 'edit_html/result.html', params)
        else:
            return redirect(to = '/edit_html')
    elif request.method == "POST":
        params = {
            'error_msg': '',
            'edit_form': EditForm()
        }

        url = request.POST['url']

        # sync_playwright()の終了処理で「Playwrightエンジン全体」を終了させ、ブラウザも終了させる
        with sync_playwright() as p:
            # ブラウザの起動
            browser = p.chromium.launch(headless = True)

            # ブラウザ内に完全に独立した新しいセッションを作成するメソッド
            # イメージ：シークレットモードを新しく立ち上げる
            context = browser.new_context(
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 新しいタブの作成
            page = context.new_page()

            try:
                # 指定したサイトに移動
                # ネットワーク通信が発生しなくなるまで待機する
                # response = page.goto(url, wait_until = 'networkidle', timeout = 3000)
                response = page.goto(url, wait_until = 'networkidle', timeout = 5000)

                # レスポンスが取得できない
                if response is None:
                    params['error_msg'] = "エラー：レスポンスを受信できませんでした"
                    return render(request, 'edit_html/index.html', params)

                # HTTPステータスコードの確認
                # ドメイン部分は存在するが、その先のアドレスがないときに実行される
                # 例）https://www.google.com/aiueo
                if not response.ok:
                    params['error_msg'] = f"エラー：サイトが見つかりません\nステータスコード：{response.status}"
                    return render(request, 'edit_html/index.html', params)

                time.sleep(2)
                full_html = page.content()

                with open(INTERMEDIATE_FILE_PATH, mode = "w", encoding = "utf-8") as f:
                    f.write(full_html)
                with open(INTERMEDIATE_FILE_PATH, mode = "r", encoding = "utf-8") as f1:
                    intermediate_html = f1.read()
                    with open(RESULT_FILE_PATH, mode = "w", encoding = "utf-8") as f2:
                        soup = BeautifulSoup(intermediate_html, "html.parser")
                        custom_style = f"""
<style>
{request.POST['style_area']}
</style>                     
"""
                        if soup.body:
                            soup.body.append(BeautifulSoup(custom_style, "html.parser"))
                        f2.write(str(soup))
                        return render(request, 'edit_html/result.html', params)
            except Exception as e:
                params['error_msg'] = f"エラー：予期せぬエラー\nエラーの詳細：\n{e}"
            finally:
                browser.close()
            return render(request, 'edit_html/index.html', params)