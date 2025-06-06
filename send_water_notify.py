# 1. 必要なライブラリ読み込み
import os
import random
import requests

# 2. LINEにメッセージを送る関数定義
def send_line_notify(message):
    line_notify_token = os.environ['LINE_TOKEN']  # GitHub Secrets からトークン取得
    line_notify_api = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Authorization': f'Bearer {line_notify_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "to": os.environ['LINE_TO'],  # 送り先ID
        "messages": [
            {
                "type": "text",
                "text": message  # 送信する本文
            }
        ]
    }
    # リクエスト発行
    requests.post(line_notify_api, headers=headers, json=payload)

# 3. ランダムメッセージを選んで送信
if __name__ == "__main__":
    messages = [
        "💧 水飲んだか？飲めよ？",
        "🚰 ちょっと手を止めて水を飲め！",
        "🫗 水分チャージしとけ！",
        "🥤 とりあえず、水飲もうな。",
        "💦 そろそろウォータータイム！"
    ]
    message = random.choice(messages)  # 1個ランダムに選ぶ
    send_line_notify(message)  # LINEに送る
