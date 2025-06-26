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
    print(f"[DEBUG] Response status: {requests.status_code}")
    print(f"[DEBUG] Response body: {requests.text}")

# 3. ランダムメッセージを選んで送信
if __name__ == "__main__":
    messages = [
        "💧 水飲んだんか？飲めよ？",
        "🚰 ちょっと手ぇ止めて水飲め！",
        "🫗 お前、水分チャージしとけって！",
        "🥤 あかん小林、水飲みにいこ。",
        "💦 ウォータータイム！汝に光があらんことを！いざゆかん、バイキングロードの上へ！"
    ]
    message = random.choice(messages)
    print(f"[DEBUG] LINE_TOKEN: {os.environ.get('LINE_TOKEN')[:10]}...")  # 一部だけ表示
    print(f"[DEBUG] LINE_TO: {os.environ.get('LINE_TO')}")
    print(f"[DEBUG] Message: {message}")
    send_line_notify(message)  # LINEに送る
