import os
import random
import requests

def send_line_notify(message):
    line_notify_token = os.environ['LINE_TOKEN']
    line_notify_api = 'https://api.line.me/v2/bot/message/push'
    headers = {
        'Authorization': f'Bearer {line_notify_token}',
        'Content-Type': 'application/json'
    }
    payload = {
        "to": os.environ['LINE_TO'],
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }
    requests.post(line_notify_api, headers=headers, json=payload)

if __name__ == "__main__":
    messages = [
        "💧 水飲んだか？飲めよ？",
        "🚰 ちょっと手を止めて水を飲め！",
        "🫗 水分チャージしとけ！",
        "🥤 とりあえず、水飲もうな。",
        "💦 そろそろウォータータイム！"
    ]
    message = random.choice(messages)
    send_line_notify(message)
