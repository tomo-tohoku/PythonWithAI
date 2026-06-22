# ２４９行目のそのままセッションが使えない問題を解決する

from django.shortcuts import render, redirect
from .forms import EditForm, ArrangeForm
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
from asgiref.sync import sync_to_async
from playwright.async_api import async_playwright
from django.contrib import messages
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def index(request):
    if request.method == "GET":
        params = {
            'error_msg_1': '',
            'error_msg_2': '',
            'edit_form': EditForm()
        }
        return render(request, 'edit_html/index.html', params)

@login_required
async def result(request):
    if request.method == "GET":
        params = {
            'error_msg_1': '',
            'error_msg_2': '',
            'edit_form': EditForm()
        }
        if "action" in request.GET:
            if request.GET["action"] == "save":
                messages.success(request, "サイトを保存しました")
                return render(request, 'edit_html/index.html', params)
            elif request.GET["action"] == "not_save":
                html_file_id = await sync_to_async(
                    request.session.get
                )("html_file_id")
                html_file = await sync_to_async(HtmlFile.objects.get)(id=html_file_id)
                await sync_to_async(html_file.delete)()
                messages.success(request, "サイトの保存を取り消しました")
                return render(request, 'edit_html/index.html', params)
        else:
            return redirect(to = '/edit_html')
    elif request.method == "POST":
        if "get-it-now" in request.POST:
            # intermediate_html が生成されて、result_html が生成されないという不均衡を解消する
            unique_id = await sync_to_async(request.session.get)("unique_id")
            if unique_id is not None:
                try:
                    html_file = await sync_to_async(HtmlFile.objects.get)(intermediate_file__endswith = unique_id + ".html")
                    if not html_file.result_file:
                        await sync_to_async(html_file.delete)()
                except HtmlFile.DoesNotExist:
                    print("データなし")

            params = {
                'error_msg_1': '',
                'error_msg_2': '',
                'edit_form': EditForm(),
                'unique_id': '',
                'title': '',
            }

            # フォームデータ取得
            url = request.POST['url']

            # async_playwright()の終了処理で「Playwrightエンジン全体」を終了させ、ブラウザも終了させる
            async with async_playwright() as p:
                # ブラウザの起動
                # headless = True でブラウザを「画面表示なし」で起動する
                browser = await p.chromium.launch(headless = True)

                # ブラウザ内に完全に独立した新しいセッションを作成するメソッド
                # イメージ：シークレットモードを新しく立ち上げる
                # user_agent でどのブラウザ・ＯＳからアクセスしているかを名乗るための文字列
                context = await browser.new_context(
                    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )

                # 新しいタブの作成
                page = await context.new_page()

                try:
                    # 指定したサイトに移動
                    # ネットワーク通信が発生しなくなるまで待機する
                    # response = page.goto(url, wait_until = 'networkidle', timeout = 5000)
                    response = await page.goto(url, wait_until = 'networkidle', timeout = 15000) # タイムアウトを変更（5/26）

                    # レスポンスが取得できない
                    if response is None:
                        params['error_msg_1'] = "エラー：レスポンスを受信できませんでした"
                        return render(request, 'edit_html/index.html', params)

                    # HTTPステータスコードの確認
                    # ドメイン部分は存在するが、その先のアドレスがないときに実行される
                    # 例）https://www.google.com/aiueo
                    if not response.ok:
                        params['error_msg_1'] = f"エラー：サイトが見つかりません\nステータスコード：{response.status}"
                        return render(request, 'edit_html/index.html', params)

                    # time.sleep(2) # time.sleep(2) はあまり良くない
                    page.wait_for_load_state('networkidle') # 追記部分

                    intermediate_html = await page.content() # page.content() の返り値は str
                    # print(intermediate_html) # デバッグ用

                    soup = BeautifulSoup(intermediate_html, "lxml")

                    html_file = HtmlFile(url = url)

                    if soup.title:
                        html_file.title = soup.title.text
                        params['title'] = soup.title.text
                    else:
                        html_file.title = "No title"
                        params['title'] = "No title"
                    # print(html_file.title) # デバッグ用

                    unique_id = uuid.uuid4()

                    # 中間のＨＴＭＬファイルのデータだけ入れる
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
                        print("styleタグが追加されました")

                    # 追記（6/22）
                    if soup.head:
                        base_tag = soup.new_tag('base')
                        parsed_url = urlparse(url)
                        base_tag['href'] = f'{parsed_url.scheme}://{parsed_url.netloc}/'
                        soup.head.append(base_tag)
                        print("baseタグが追加されました")

                    result_html = str(soup)

                    # アレンジした後のＨＴＭＬファイルのデータだけ入れる
                    html_file.result_file.save(
                        f'result_{unique_id}.html',
                        ContentFile(result_html.encode("utf-8")),
                        save = False
                    )

                    # これにしたらうまくいった（5/28）
                    # これで html_file をデータベースに入れる
                    with ThreadPoolExecutor() as executor:
                        executor.submit(html_file.save).result()
                    
                    # セッションがそのまま使えない問題を解決する
                    await sync_to_async(request.session.__setitem__)(
                        "html_file_id",
                        html_file.id
                    )
                    
                    params['unique_id'] = unique_id

                    return render(request, 'edit_html/result.html', params)
                except Exception as e:
                    traceback.print_exc()
                    params['error_msg_1'] = f"エラー：予期せぬエラー\nエラーの詳細：\n{e}"
                finally:
                    browser.close()
                return render(request, 'edit_html/index.html', params)
        elif "arrange-later" in request.POST:
            params = {
                'error_msg_1': '',
                'error_msg_2': '',
                'edit_form': EditForm(),
                'unique_id': '',
                'title': '',
            }

            url = await sync_to_async(request.session.get)("url")
            html_file_id = await sync_to_async(request.session.get)("html_file_id")
            intermediate_file = await sync_to_async(request.session.get)("intermediate_file")
            unique_id = await sync_to_async(request.session.get)("unique_id")

            soup = BeautifulSoup(intermediate_file, "lxml")

            html_file = await sync_to_async(HtmlFile.objects.get)(id = html_file_id)

            tag = request.POST.get('tag', '')
            selected_class = request.POST.get('selected_class', '')
            selected_id = request.POST.get('selected_id', '')
            attr = request.POST.get('attr', '')
            style_area = request.POST.get('style_area', '')

            if soup.head:
                base_tag = soup.new_tag('base')
                parsed_url = urlparse(url)
                base_tag['href'] = f'{parsed_url.scheme}://{parsed_url.netloc}/'
                soup.head.append(base_tag)
                print("baseタグが追加されました")

            if tag == '' and selected_class == '' and selected_id == '':
                select_str = '*'
            else:
                selected_class = f'.{selected_class}' if selected_class != '' else ''
                selected_id = f'#{selected_id}' if selected_id != '' else ''
                select_str = f'{tag}{selected_class}{selected_id}'
            tags = soup.select(select_str)
            for tag in tags:
                old_style = tag.get(attr, "")
                new_style = style_area
                tag[attr] = old_style + new_style # 古いスタイルと結合
            
            result_html = str(soup)

            # アレンジした後のＨＴＭＬファイルのデータだけ入れる
            with ThreadPoolExecutor() as executor:
                executor.submit(
                    html_file.result_file.save,
                    f'result_{unique_id}.html',
                    ContentFile(result_html.encode("utf-8")),
                    save = True
                ).result()
            
            params['unique_id'] = unique_id
            return render(request, 'edit_html/result.html', params)

# 取得したＨＴＭＬデータをアレンジする関数
@login_required
async def arrange(request):
    if request.method == "POST":
        # intermediate_html が生成されて、result_html が生成されないという不均衡を解消する
        unique_id = await sync_to_async(request.session.get)("unique_id")
        if unique_id is not None:
            try:
                html_file = await sync_to_async(HtmlFile.objects.get)(intermediate_file__endswith = unique_id + ".html")
                if not html_file.result_file:
                    await sync_to_async(html_file.delete)()
            except HtmlFile.DoesNotExist:
                print("データなし")

        params = {
            'error_msg_1': '',
            'error_msg_2': '',
            'edit_form': EditForm(),
            'html_code': '',
            'arrange_form': ArrangeForm(),
        }
        # フォームデータ取得
        url = request.POST['url']

        # sync_playwright()の終了処理で「Playwrightエンジン全体」を終了させ、ブラウザも終了させる
        async with async_playwright() as p:
            # ブラウザの起動
            # headless = True でブラウザを「画面表示なし」で起動する
            browser = await p.chromium.launch(headless = True)

            # ブラウザ内に完全に独立した新しいセッションを作成するメソッド
            # イメージ：シークレットモードを新しく立ち上げる
            # user_agent でどのブラウザ・ＯＳからアクセスしているかを名乗るための文字列
            context = await browser.new_context(
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )

            # 新しいタブの作成
            page = await context.new_page()

            try:
                # 指定したサイトに移動
                # ネットワーク通信が発生しなくなるまで待機する
                # response = page.goto(url, wait_until = 'networkidle', timeout = 5000)
                response = await page.goto(url, wait_until = 'networkidle', timeout = 15000) # タイムアウトを変更（5/26）

                # レスポンスが取得できない
                if response is None:
                    params['error_msg_2'] = "エラー：レスポンスを受信できませんでした"
                    return render(request, 'edit_html/index.html', params)

                # HTTPステータスコードの確認
                # ドメイン部分は存在するが、その先のアドレスがないときに実行される
                # 例）https://www.google.com/aiueo
                if not response.ok:
                    params['error_msg_2'] = f"エラー：サイトが見つかりません\nステータスコード：{response.status}"
                    return render(request, 'edit_html/index.html', params)

                # time.sleep(2) # time.sleep(2) はあまり良くない
                page.wait_for_load_state('networkidle') # 追記部分

                intermediate_html = await page.content() # page.content() の返り値は str
                # print(intermediate_html) # デバッグ用

                soup = BeautifulSoup(intermediate_html, "lxml")
                params['html_code'] = soup.prettify()

                html_file = HtmlFile(url = url)

                if soup.title:
                    html_file.title = soup.title.text
                else:
                    html_file.title = "No title"
                # print(html_file.title) # デバッグ用

                unique_id = uuid.uuid4()

                # 中間のＨＴＭＬファイルのデータだけ入れる
                html_file.intermediate_file.save(
                    f'intermediate_{unique_id}.html',
                    ContentFile(intermediate_html.encode("utf-8")),
                    save = False
                )

                with ThreadPoolExecutor() as executor:
                    executor.submit(html_file.save).result()

                # セッションがそのまま使えない問題を解決する
                await sync_to_async(request.session.__setitem__)(
                    "html_file_id",
                    html_file.id
                )

                # 別の関数で共有できるようにセッションを使う
                request.session["url"] = url
                request.session["intermediate_file"] = str(soup)
                request.session["unique_id"] = str(unique_id)

                return render(request, 'edit_html/arrange.html', params)
            except Exception as e:
                traceback.print_exc()
                params['error_msg_2'] = f"エラー：予期せぬエラー\nエラーの詳細：\n{e}"
            finally:
                await browser.close()
            return render(request, 'edit_html/index.html', params)