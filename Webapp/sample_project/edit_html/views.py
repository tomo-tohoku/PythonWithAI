from django.shortcuts import render, redirect
from .forms import EditForm
from django.http import HttpResponse

from bs4 import BeautifulSoup

from playwright.sync_api import sync_playwright
import os
from pathlib import Path

# 追加（5/27）
import uuid
from .models import HtmlFile
from django.core.files.base import ContentFile
import traceback
from concurrent.futures import ThreadPoolExecutor

# 追加（6/22）
from urllib.parse import urlparse # ＵＲＬ名から https://ドメイン名/ の部分を取り出す

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

        # フォームデータ取得
        url = request.POST['url']

        # sync_playwright()の終了処理で「Playwrightエンジン全体」を終了させ、ブラウザも終了させる
        with sync_playwright() as p:
            # ブラウザの起動
            # headless = True でブラウザを「画面表示なし」で起動する
            browser = p.chromium.launch(headless = True)

            # ブラウザ内に完全に独立した新しいセッションを作成するメソッド
            # イメージ：シークレットモードを新しく立ち上げる
            # user_agent でどのブラウザ・ＯＳからアクセスしているかを名乗るための文字列
            context = browser.new_context(
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 新しいタブの作成
            page = context.new_page()

            try:
                # 指定したサイトに移動
                # ネットワーク通信が発生しなくなるまで待機する
                # response = page.goto(url, wait_until = 'networkidle', timeout = 5000)
                response = page.goto(url, wait_until = 'networkidle', timeout = 15000) # タイムアウトを変更（5/26）

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

                # time.sleep(2) # time.sleep(2) はあまり良くない
                page.wait_for_load_state('networkidle') # 追記部分

                intermediate_html = page.content() # page.content() の返り値は str
                # print(intermediate_html) # デバッグ用

                soup = BeautifulSoup(intermediate_html, "lxml")

                html_file = HtmlFile(url = url)

                if soup.title:
                    html_file.title = soup.title.text
                else:
                    html_file.title = "No title"
                # print(html_file.title) # デバッグ用

                unique_id = uuid.uuid4()

                html_file.intermediate_file.save(
                    f'intermediate_{unique_id}.html',
                    ContentFile(intermediate_html.encode("utf-8")),
                    save = False
                )

                custom_style = request.POST.get('style_area', '')
                if custom_style and soup.body: # custom_style が空文字でなく、かつ body タグが存在するなら
                    style_tag = soup.new_tag('style')
                    style_tag.string = custom_style
                    soup.body.append(style_tag)

                # 追記（6/22）
                if custom_style and soup.head:
                    base_tag = soup.new_tag('base')
                    parsed_url = urlparse(url)
                    base_tag['href'] = f'{parsed_url.scheme}://{parsed_url.netloc}/'
                    soup.head.append(base_tag)

                result_html = str(soup)

                html_file.result_file.save(
                    f'result_{unique_id}.html',
                    ContentFile(result_html.encode("utf-8")),
                    save = False
                )

                # これにしたらうまくいった（5/28）
                with ThreadPoolExecutor() as executor:
                    executor.submit(html_file.save).result()

                return HttpResponse(result_html)
            except Exception as e:
                traceback.print_exc()
                params['error_msg'] = f"エラー：予期せぬエラー\nエラーの詳細：\n{e}"
            finally:
                browser.close()
            return render(request, 'edit_html/index.html', params)