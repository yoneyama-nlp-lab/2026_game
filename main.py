
import asyncio
import pygame, sys
from pygame.locals import *
import os
import platform
import json
import textwrap
from datetime import datetime

# APIに接続するためのJavaScript（これは変更しないこと）
platform.window.eval("""
window.postRequest = function* (url, body, headers) {
    let result = null;
    fetch(url, {
        method: "POST",
        headers: JSON.parse(headers),
        body: body})
    .then(async response => {
        result = JSON.stringify({
            status: response.status,
            body: await response.text()});})
    .catch(error => {
        result = JSON.stringify({
            status: 0,
            body: String(error)});});
    while (result === null) {
        yield;}
    yield result;};""")


# GPTに接続するためのユーザー定義関数（これは変更しないこと）
async def GPT(answer_num):
    print('GPT接続開始')

    # 現在時刻を基準に1から4の数字を取得
    random_num = (datetime.now().second % 4) + 1

    # プロンプト
    role = 'あなたは就職に関する' + str(answer_num) + '択クイズを作成するシステムです。'
    prompt = f'''テーマ：就職の面接またはエントリーシートにおける言葉遣い
    ・問題文と解説文は全て全角文字で作成してください。
    ・問題文だけを読んで回答できる内容にしてください。
    ・選択肢の文や解説文の中には、選択肢の回答番号や回答記号は含めない。
    ・正解は必ず{random_num}番になるように作ってください。
    ・正解は必ず1つだけにしてください。
    ・不正解の選択肢は、明らかに不自然なものではなく、もっともらしいものにしてください。
    ・不正解の選択肢に「初心者がやりがちな典型的な勘違いや、一見正しそうに見える誤った概念を含むもの」を含めてください。
    ・不正解の選択肢に「文脈はあっているが、キーワード（専門用語）だけを関する別の用語にすり替えたもの」または「記述自体は正しいものの、問題の条件を一部満たしてない（説明が不足している）もの」を含めてください。
    ・解説文は、正解や不正解の理由のみを端的に示してください。
    '''

    response = await platform.jsiter(
        platform.window.postRequest(
            'https://script.google.com/macros/s/AKfycbyvexWR3H2PSoRuBQArk8pbZaEqAAUrF1vRy3kpu-ligYwsaVOUeRbRMhAOIzkBulT6bA/exec',
            json.dumps(
                {'model': 'gpt-5.6-luna',
                'input': [{'role': 'developer', 'content': role},
                {'role': 'user', 'content': prompt}],
                'text': {'format': {'type': 'json_schema',
                    'name': 'quiz',
                    'strict': True,
                    'schema': {'type': 'object',
                    'properties': {'question': {'type': 'string'},
                    'choices': {'type': 'array',
                        'items': {'type': 'string'},
                        'minItems': answer_num,
                        'maxItems': answer_num},
                    'answer': {
                        'type': 'integer',
                        'enum': [x for x in range(1, answer_num+1)]},
                    "explanation":{'type': 'array',
                        'items': {'type': 'string'},
                        'minItems': answer_num,
                        'maxItems': answer_num}},
                    'required': ['question', 'choices', 'answer', 'explanation'],
                    'additionalProperties': False}}}}),
            json.dumps({'Content-Type': 'text/plain'})))

    response = json.loads(response)

    # GASの通信ステータスを確認
    if response['status'] != 200:
        return response

    # GASから返されたJSONを解析
    response = json.loads(response['body'])

    # OpenAI APIのステータスコードを確認
    if response['status'] == 200:
        result = json.loads([x for x in json.loads(response['body'])['output'] if x['type']=='message'][0]['content'][0]['text'])
        return result
    else:
        return response


# Pygameの初期化
pygame.init()
clock = pygame.time.Clock()
screen = pygame.display.set_mode((600, 600))
font = pygame.font.Font('fonts-japanese-gothic.ttf', 27)
# 解説などの長い文章用に少し小さいフォントも用意
small_font = pygame.font.Font('fonts-japanese-gothic.ttf', 22)

# ボタンの位置と大きさを決める (x座標, y座標, 幅, 高さ)
start_rect = pygame.Rect(260, 200, 120, 50)
how_to_rect = pygame.Rect(260, 320, 120, 50)


async def main():
    # 選択肢の数
    answer_num = 4

    # 現在どの画面にいるかを管理する変数
    # 'title' = タイトル, 'quiz' = クイズ画面, 'correct' = 正解画面, 'commentary' = 解説画面, 'how_to' = 遊び方画面
    game_screen = 'title' # 最初はタイトル

    # タスク管理用の初期変数
    gpt_task = None
    quiz_data = {}
    answer_idx = 0

    # 全角変換用
    trans_table = str.maketrans("0123456789", "０１２３４５６７８９")

    # 合計問題数
    total_question_count = 3

    # 問題数カウント
    question_count = 0

    while True:
        # フリーズ防止のため、毎フレーム必ずイベント（マウスやキーの入力）を取得する
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            # キーボードが押されたときの処理
            elif event.type == KEYDOWN:
                # --- 1. タイトル画面のキー判定 ---
                if game_screen == 'title':
                    if event.key == K_1:      # 1で始める
                        game_screen = 'quiz'
                    elif event.key == K_2:    # 2で遊び方
                        game_screen = 'how_to'

                # --- 2. クイズ画面（quiz）のキー判定 ---
                elif game_screen == 'quiz' and len(quiz_data) != 0:
                    user_choice = None
                    if event.key == K_1:      # 1 = 1番目の選択肢
                        user_choice = 0
                    elif event.key == K_2:    # 2 = 2番目の選択肢
                        user_choice = 1
                    elif event.key == K_3:    # 3 = 3番目の選択肢
                        user_choice = 2
                    elif event.key == K_4:    # 4 = 4番目の選択肢
                        user_choice = 3

                    # いずれかのキーが押された場合のみ正誤判定を行う
                    if user_choice is not None:
                        if user_choice == answer_idx:
                            game_screen = 'correct'       # 正解なら correct へ！
                        else:
                            game_screen = 'commentary'   # 間違いなら 解説画面 へ！

                # --- 3. 解説画面（commentary）のキー判定 ---
                elif game_screen == 'commentary':
                    # W, A, S, D のいずれかが押されたらタイトルに戻る
                    if event.key in [K_1, K_2, K_3, K_4]:
                        # 問題文リセット
                        quiz_data = {}
                        if question_count == total_question_count:
                            # 全問題終了
                            game_screen = 'title'
                        else:
                            # 次の問題へ
                            game_screen = 'quiz'

                # --- 4. correctのキー判定 ---
                elif game_screen == 'correct':
                    # W, A, S, D のいずれかが押されたらタイトルに戻る
                    if event.key in [K_1, K_2, K_3, K_4]:
                        # 問題文リセット
                        quiz_data = {}
                        if question_count == total_question_count:
                            # 全問題終了
                            game_screen = 'title'
                        else:
                            # 次の問題へ
                            game_screen = 'quiz'

                # --- 5. how_toのキー判定 ---
                elif game_screen == 'how_to':
                    # W, A, S, D のいずれかが押されたらタイトルに戻る
                    if event.key in [K_1, K_2, K_3, K_4]:
                        game_screen = 'title'

        # ==================================================
        # 1. タイトル画面の処理
        # ==================================================
        if game_screen == 'title':
            # GPTへの接続タスク
            if gpt_task is None:
                gpt_task = asyncio.create_task(GPT(answer_num))

            screen.fill((240, 248, 255)) # 背景色（うすい青）

            # ボタンの文字を描画
            screen.blit(font.render('始める[1]', True, (0, 0, 0)), (start_rect.x, start_rect.y))
            screen.blit(font.render('遊び方[2]', True, (0, 0, 0)), (how_to_rect.x, how_to_rect.y))


        # ==================================================
        # 2. ゲーム画面（quiz：クイズ回答）の処理
        # ==================================================

        # GPTの処理が終わっていない
        elif game_screen == 'quiz' and len(quiz_data) == 0 and not gpt_task.done():
            screen.fill((200, 255, 200)) # 背景色（うすい緑）
            screen.blit(font.render('問題文読込中...', True, (0, 0, 0)), (60, 320))

        # GPTの処理が完了済
        elif game_screen == 'quiz' and (len(quiz_data) != 0 or gpt_task.done()):
            screen.fill((200, 255, 200)) # 背景色（うすい緑）

            # GPTから問題文を取得
            if len(quiz_data) == 0:
                quiz_data = await gpt_task

                # 問題数カウント
                question_count += 1

                # GPTへの接続タスク（次の問題の取得を始める）
                gpt_task = asyncio.create_task(GPT(answer_num))

                print(quiz_data) # 確認用にコンソールにGPTからの取得結果を表示
                answer_idx = quiz_data['answer'] - 1 # リストの最初は0番目

            # 問題文の表示
            y = 40 # 一行目の表示位置
            question_text = '問' + str(question_count).translate(trans_table) + '：' + quiz_data['question']
            for textwrap_text in textwrap.wrap(question_text, 18):
                screen.blit(font.render(textwrap_text, True, (0, 0, 0)), (40, y))
                # 18文字ごとに改行
                y += font.get_linesize()
            # 選択肢の間で1行改行
            y += font.get_linesize()

            key_guides = [" [1]", " [2]", " [3]", " [4]"]

            # 選択肢の表示（長い場合に備えて少し小さいフォントで表示）
            y = 200 # 一行目の表示位置
            for i, s in enumerate(quiz_data["choices"]):
                choices = str(i+1).translate(trans_table) + '．' + s + key_guides[i]
                # 改行を考慮した画面描画
                for textwrap_text in textwrap.wrap(choices, 18):
                    screen.blit(small_font.render(textwrap_text, True, (0, 0, 0)), (60, y))
                    # 18文字ごとに改行
                    y += small_font.get_linesize()
                # 選択肢の間で1行改行
                y += small_font.get_linesize()

        # ==================================================
        # 解説画面（commentary）の処理
        # ==================================================
        elif game_screen == 'commentary':
            screen.fill((255, 230, 230)) # 背景色（うすい赤・ピンク）

            # メッセージと解説文の表示
            screen.blit(font.render('残念！不正解...', True, (200, 0, 0)), (150, 50))
            screen.blit(font.render('【解説】', True, (0, 0, 0)), (50, 150))

            # 解説テキスト（長い場合に備えて少し小さいフォントで表示）
            y = 240 # 一行目の表示位置
            for i, s in enumerate(quiz_data["explanation"]):
                if i == answer_idx:
                    result_str = '正解。'
                else:
                    result_str = '不正解。'
                explanation = str(i+1).translate(trans_table) + '．' + result_str + s
                # 改行を考慮した画面描画
                for textwrap_text in textwrap.wrap(explanation, 20):
                    screen.blit(small_font.render(textwrap_text, True, (0, 0, 0)), (50, y))
                    # 20文字ごとに改行
                    y += small_font.get_linesize()
                # 選択肢の間で1行改行
                y += small_font.get_linesize()

            # 案内メッセージをキーボード用に変更
            screen.blit(font.render('【1,2,3,4のどれかで次へ】', True, (100, 100, 100)), (100, 530))

        # ==================================================
        # 正解画面（correct）の処理
        # ==================================================
        elif game_screen == 'correct':
            screen.fill((255, 255, 200)) # 背景色（うすい黄色）

            screen.blit(font.render('正解画面', True, (0, 128, 0)), (250, 30))
            # 案内メッセージをキーボード用に変更
            screen.blit(font.render('【1,2,3,4のどれかで次へ】', True, (100, 100, 100)), (110, 400))

        # ==================================================
        # 3. 遊び方画面（how_to）の処理
        # ==================================================
        elif game_screen == 'how_to':
            screen.fill((230, 230, 230)) # 背景色（うすい灰色）
            screen.blit(font.render('ここは遊び方の説明画面です！', True, (0, 0, 0)), (50, 200))
            # 案内メッセージをキーボード用に変更
            screen.blit(font.render('【1,2,3,4のどれかでタイトルへ】', True, (100, 100, 100)), (50, 400))

        # 画面を実際に更新する
        pygame.display.update()
        clock.tick(30)
        await asyncio.sleep(0)

# ゲームの実行
asyncio.run(main())
