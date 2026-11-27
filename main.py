
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


# GPTに接続するためのユーザー定義関数（基本的に変更しない）
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
    ・不正解の選択肢に「文脈はあっているが、キーワード（専門用語）だけを関連する別の用語にすり替えたもの」または「記述自体は正しいものの、問題の条件を一部満たしていないもの」を含めてください。
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
        result = json.loads(
            [
                x for x in json.loads(response['body'])['output']
                if x['type'] == 'message'
            ][0]['content'][0]['text']
        )
        return result
    else:
        return response


# Pygameの初期化
pygame.init()

clock = pygame.time.Clock()
screen = pygame.display.set_mode((600, 600))

font = pygame.font.Font('fonts-japanese-gothic.ttf', 23)
small_font = pygame.font.Font('fonts-japanese-gothic.ttf', 16)


# ボタンの位置と大きさ
start_rect = pygame.Rect(260, 200, 120, 50)
how_to_rect = pygame.Rect(260, 320, 120, 50)


async def main():

    # 選択肢の数
    answer_num = 4

    # 現在の画面
    # title = タイトル
    # quiz = クイズ画面
    # correct = 正解画面
    # commentary = 解説画面
    # how_to = 遊び方画面
    # game_over = ゲームオーバー画面
    game_screen = 'title'

    # GPTのタスク管理
    gpt_task = None

    # クイズデータ
    quiz_data = {}

    # 正解番号
    answer_idx = 0

    # 全角変換用
    trans_table = str.maketrans(
        "0123456789",
        "０１２３４５６７８９"
    )

    # 合計問題数
    total_question_count = 3
    # 問題数
    question_count = 0

    # LIFE
    max_life = 3
    life = max_life

    # ゲーム開始
    while True:
        events = pygame.event.get()
        for event in events:

            if event.type == QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == KEYDOWN:

                # ----------------------------
                # 1. タイトル画面
                # ----------------------------
                if game_screen == 'title':
                    if event.key == K_1:

                        # LIFEを初期化
                        life = max_life

                        # 問題数を初期化
                        question_count = 0

                        # クイズデータを初期化
                        quiz_data = {}

                        # クイズ画面へ
                        game_screen = 'quiz'

                    elif event.key == K_2:
                        # 遊び方画面へ
                        game_screen = 'how_to'

                # ----------------------------
                # 2. クイズ画面
                # ----------------------------
                elif game_screen == 'quiz' and len(quiz_data) != 0:
                    user_choice = None

                    if event.key == K_1:
                        user_choice = 0

                    elif event.key == K_2:
                        user_choice = 1

                    elif event.key == K_3:
                        user_choice = 2

                    elif event.key == K_4:
                        user_choice = 3

                    # 1～4が押された場合のみ判定
                    if user_choice is not None:

                        # 正解の場合
                        if user_choice == answer_idx:
                            game_screen = 'correct'

                        # 不正解の場合
                        else:
                            # LIFEを1減らす
                            life -= 1

                            # LIFEが0以下の場合
                            if life <= 0:
                                game_screen = 'game_over'

                            # LIFEが残っている場合
                            else:
                                game_screen = 'commentary'

                # ----------------------------
                # 3. 解説画面
                # ----------------------------
                elif game_screen == 'commentary':
                    if event.key in [K_1, K_2, K_3, K_4]:
                        quiz_data = {}

                        if question_count == total_question_count:
                            game_screen = 'title'

                        else:
                            game_screen = 'quiz'

                # ----------------------------
                # 4. 正解画面
                # ----------------------------
                elif game_screen == 'correct':
                    if event.key in [K_1, K_2, K_3, K_4]:
                        quiz_data = {}

                        if question_count == total_question_count:
                            game_screen = 'title'
                        else:
                            game_screen = 'quiz'

                # ----------------------------
                # 5. 遊び方画面
                # ----------------------------
                elif game_screen == 'how_to':
                    if event.key in [K_1, K_2, K_3, K_4]:
                        game_screen = 'title'

                # ----------------------------
                # 6. ゲームオーバー画面
                # ----------------------------
                elif game_screen == 'game_over':
                    if event.key == K_1:

                        life = max_life
                        question_count = 0
                        quiz_data = {}
                        game_screen = 'title'

        # ==================================================
        # 1. タイトル画面
        # ==================================================
        if game_screen == 'title':
            screen.fill((240, 248, 255))

            # GPTへの接続タスク
            if gpt_task is None:
                gpt_task = asyncio.create_task(GPT(answer_num))

            # タイトル表示
            screen.blit(
                font.render('始める[1]', True, (0, 0, 0)),
                (start_rect.x, start_rect.y))

            screen.blit(
                font.render('遊び方[2]', True, (0, 0, 0)),
                (how_to_rect.x, how_to_rect.y))

        # ==================================================
        # 2. クイズ画面
        # ==================================================
        elif game_screen == 'quiz':
            screen.fill((200, 255, 200))

            # GPTの問題取得
            if len(quiz_data) == 0:
                # GPTの処理が終わっていない場合
                if gpt_task is None or not gpt_task.done():

                    screen.blit(font.render('問題文読込中...',True,(0, 0, 0)),(60, 320))

                # GPTの処理が完了した場合
                else:
                    quiz_data = await gpt_task

                    # 問題数をカウント
                    question_count += 1

                    # GPTへの次の問題取得を開始
                    gpt_task = asyncio.create_task(GPT(answer_num))

                    print(quiz_data)

                    # GPTの取得結果を確認
                    if 'answer' not in quiz_data:
                        screen.fill((255, 230, 230))
                        screen.blit(font.render('問題の取得に失敗しました',True,(200, 0, 0)),(50, 250))
                        screen.blit(font.render('タイトルに戻ってください',True,(0, 0, 0)),(50, 320))
                        game_screen = 'game_over'

                    else:
                        # 正解番号を取得
                        answer_idx = quiz_data['answer'] - 1

            # 問題データがある場合
            if len(quiz_data) != 0 and 'answer' in quiz_data:
                # ライフ表示
                # LIFE表示
                screen.blit(
                    font.render(
                        'ライフ：' + str(life),
                        True,
                        (255, 0, 0)
                    ),
                    (400, 10)
                )
                # 問題文表示
                y = 40

                question_text = (
                    '問'
                    + str(question_count).translate(trans_table)
                    + '：'
                    + quiz_data['question']
                )
                # 〇文字ごとに改行(問題文)
                for textwrap_text in textwrap.wrap(question_text, 23):
                    screen.blit(font.render(textwrap_text,True,(0, 0, 0)),(40, y))
                    y += font.get_linesize()
                y += font.get_linesize()

                # 選択肢
                key_guides = [" [1]"," [2]"," [3]"," [4]"]

                y = 400
                for i, s in enumerate(quiz_data["choices"]):

                    choices = (
                        str(i + 1).translate(trans_table)
                        + '．'
                        + s
                    )
                    # 〇文字ごとに改行(選択)
                    for textwrap_text in textwrap.wrap(choices, 30):
                        screen.blit(small_font.render(textwrap_text,True,(0, 0, 0)),(60, y))
                        y += small_font.get_linesize()
                    y += small_font.get_linesize()

        # ==================================================
        # 3. 解説画面
        # ==================================================
        elif game_screen == 'commentary':
            screen.fill((255, 230, 230))
            # メッセージ
            screen.blit(font.render('残念！不正解...',True,(200, 0, 0)),(150, 50))
            # LIFE表示
            screen.blit(font.render('残りライフ：' + str(life),True,(255, 0, 0)),(200, 100))
            screen.blit(font.render('【解説】', True, (0, 0, 0)),(50, 150))

            # 解説文
            y = 210

            for i, s in enumerate(quiz_data["explanation"]):
                if i == answer_idx:
                    result_str = '正解。'
                else:
                    result_str = '不正解。'

                explanation = (
                    str(i + 1).translate(trans_table)
                    + '．'
                    + result_str
                    + s
                )
                # 〇文字ごとに改行(解説)
                for textwrap_text in textwrap.wrap(explanation, 30):
                    screen.blit(small_font.render(textwrap_text,True,(0, 0, 0)),(50, y))
                    y += small_font.get_linesize()
                y += small_font.get_linesize()

            screen.blit(font.render('【1,2,3,4のどれかで次へ】',True,(100, 100, 100)),(100, 530))

        # ==================================================
        # 4. 正解画面
        # ==================================================
        elif game_screen == 'correct':
            screen.fill((255, 255, 200))
            screen.blit(font.render('正解！',True,(0, 128, 0)),(250, 150))
            screen.blit(font.render('ライフ：' + str(life),True,(255, 0, 0)),(230, 220))
            screen.blit(font.render('【1,2,3,4のどれかで次へ】',True,(100, 100, 100)),(110, 400))

        # ==================================================
        # 5. 遊び方画面
        # ==================================================
        elif game_screen == 'how_to':
            screen.fill((230, 230, 230))
            screen.blit(font.render('ここは遊び方の説明画面です！',True,(0, 0, 0)),(50, 200))
            screen.blit(small_font.render('数字の1～4で回答してください。',True,(0, 0, 0)),(50, 280))
            screen.blit(small_font.render('不正解になるとLIFEが1減ります。',True,(0, 0, 0)),(50, 330))
            screen.blit(small_font.render('LIFEが0になるとゲームオーバーです。',True,(0, 0, 0)),(50, 380))
            screen.blit(font.render('【1,2,3,4のどれかでタイトルへ】',True,(100, 100, 100)),(50, 450))

        # ==================================================
        # 6. ゲームオーバー画面
        # ==================================================
        elif game_screen == 'game_over':
            screen.fill((50, 50, 50))

            screen.blit(font.render('GAME OVER',True,(255, 0, 0)),(200, 200))
            screen.blit(font.render('ライフがなくなりました',True,(255, 255, 255)),(120, 280))
            screen.blit(font.render('【1でタイトルへ戻る】',True,(255, 255, 255)),(130, 400))

        # ==================================================
        # 画面更新
        # ==================================================
        pygame.display.update()
        clock.tick(30)
        await asyncio.sleep(0)


# ゲームの実行
asyncio.run(main())
