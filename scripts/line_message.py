"""LINEの一覧URL通知用JSON生成"""

import json
import os
from pathlib import Path
import sys


def main():
    """認証情報を含めずに通知先と従来の本文をJSONファイルへ出力"""
    payload = {
        "to": os.environ["LINE_TO"],
        "messages": [{
            "type": "text",
            "text": "\u2705 金属バット公演一覧が更新されました！\nhttps://rockn-git-hub.github.io/fany-scheduler/kinzoku_bat_events.html",
        }],
    }
    Path(sys.argv[1]).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
