import time  # 遷移後の待機用
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime

# セットアップ
options = Options()
options.add_argument("--headless")  # デバッグ時は外す
driver = webdriver.Chrome(options=options)
driver.get("https://ticket.fany.lol/search/event?keywords=金属バット")

wait = WebDriverWait(driver, 10)

# 「もっと見る」押し続ける
while True:
    try:
        old_count = len(driver.find_elements(By.CLASS_NAME, "fany_performanceListBox__headerTitle"))
        more_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, ".more-btn button")))
        more_button.click()
        WebDriverWait(driver, 10).until(
            lambda d: len(d.find_elements(By.CLASS_NAME, "fany_performanceListBox__headerTitle")) > old_count
        )
    except:
        break


# 公演リストを取得
performances = driver.find_elements(By.CLASS_NAME, "fany_performanceListBox__outline")[0].find_elements(By.XPATH, "./div")

events_list = []

for perf in performances:
    try:
        title = perf.find_element(By.CLASS_NAME, "fany_performanceListBox__headerTitle").text.strip()

        # ✅ 公演日を確実に取得
        date_text = perf.find_element(By.CLASS_NAME, "fany_performanceListBox__headerPerformanceDate").text.strip()
        date_str = date_text.split("(")[0].strip()
        event_date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()

        venue = perf.find_element(By.CLASS_NAME, "fany_performanceListBox__headerVenue").text.strip()

        # 販売ステータス（複数パターン対応）
        sale_status = "不明"
        for cls in ["fany_icon__sold", "fany_icon__soldout", "fany_icon__coming"]:
            found = perf.find_elements(By.CLASS_NAME, cls)
            if found:
                sale_status = found[0].text.strip()
                break

        # 詳細リンク取得
        link_elem = perf.find_element(By.CSS_SELECTOR, ".fany_g-ticketInfo a")
        detail_link = link_elem.get_attribute("href") if link_elem else None

        # 公演名フィルタ
        if '本公演' in title:
            continue

        # 会場フィルタ
        if not ('大阪府' in venue or '京都府' in venue):
            continue

        events_list.append({
            "title": title,
            "date": event_date,
            "date_text": date_text,
            "venue": venue,
            "sale_status": sale_status,
            "detail_link": detail_link,
        })

    except Exception as e:
        print(f"⚠️ スキップ（理由: {e}）")
        continue

# ✅ 各イベントの価格情報を取得（後から別途アクセス）
for event in events_list:
    prices = []
    open_start_time = ""

    if event["detail_link"]:
        try:
            driver.get(event["detail_link"])
            WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "g-sellItems_item")))

            # 開場/開演時間を取得
            try:
                summary_box = driver.find_element(By.CLASS_NAME, "g-itemSet_summary")
                body_elements = summary_box.find_elements(By.CLASS_NAME, "g-itemSet_body")
                for b in body_elements:
                    text = b.text.strip()
                    if "開場" in text and "開演" in text:
                        open_start_time = text
                        break
            except:
                open_start_time = ""

            # チケット情報を取得
            ticket_sections = driver.find_elements(By.CLASS_NAME, "g-sellItems_item")
            for section in ticket_sections:
                try:
                    seat_type_el = section.find_element(By.TAG_NAME, "dt")
                    seat_type = driver.execute_script("return arguments[0].textContent;", seat_type_el).strip()

                    ticket_divs = section.find_elements(By.CLASS_NAME, "g-sellItems_ticket")
                    for ticket_div in ticket_divs:
                        try:
                            ticket_type_el = ticket_div.find_element(By.CLASS_NAME, "g-sellItems_type")
                            price_el = ticket_div.find_element(By.CLASS_NAME, "g-sellItems_price")

                            ticket_type = driver.execute_script("return arguments[0].textContent;",
                                                                ticket_type_el).strip()
                            price = driver.execute_script("return arguments[0].textContent;", price_el).strip()

                            if seat_type == "":
                                prices.append(f"{ticket_type}：{price}")
                            else:
                                prices.append(f"{seat_type}／{ticket_type}：{price}")

                        except Exception as e:
                            prices.append(f"{seat_type}／取得失敗：{e}")
                except Exception as e:
                    prices.append(f"取得失敗：{e}")
        except Exception as e:
            prices.append(f"価格取得エラー: {e}")
    else:
        prices.append("詳細リンクなし")

    event["prices"] = prices
    event["open_start_time"] = open_start_time

driver.quit()

# 昇順
events_list.sort(key=lambda x: x["date"] if x["date"] else datetime.date.max)

# 降順
events_list.sort(key=lambda x: x["date"] if x["date"] else datetime.date.min, reverse=True)


print("\n🎭 **金属バット公演一覧（日時昇順）** 🎭\n" + "=" * 50)
for e in events_list:
    if '本公演' in e['title']:
        continue
    print(f"📅 【日程】{e['date_text']}")
    print(f"🎭 【公演名】{e['title']}")
    print(f"📍 【会場】{e['venue']}")
    print(f"🎫 【販売状況】{e['sale_status']}")
    print(f"🕒 【開場/開演】{e['open_start_time']}")
    print(f"💴 【チケット価格】")
    for p in e["prices"]:
        print(f"　- {p}")
        break # 先頭の1つだけ出力
    print(f"🔗 【詳細リンク】{e['detail_link']}")
    print("-" * 50)



html_output_path = "kinzoku_bat_events.html"

html_content = '''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>金属バット公演一覧</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
    <h1 class="mb-4 text-center">金属バット公演一覧</h1>
    <div class="row g-4">
'''

for e in events_list:
    if '本公演' in e['title']:
        continue

    price_line = e['prices'][0] if e['prices'] else "情報なし"
    html_content += f'''
        <div class="col-md-6 col-lg-4">
            <div class="card shadow-sm h-100">
                <div class="card-body">
                    <h5 class="card-title">{e['title']}</h5>
                    <p class="card-text">
                        📅 <strong>日程：</strong>{e['date_text']}<br>
                        📍 <strong>会場：</strong>{e['venue']}<br>
                        🕒 <strong>開場/開演：</strong>{e.get('open_start_time', '不明')}<br>
                        🎫 <strong>販売状況：</strong>{e['sale_status']}<br>
                        💴 <strong>価格：</strong>{price_line}
                    </p>
                    <a href="{e['detail_link']}" target="_blank" rel="noopener noreferrer" class="btn btn-primary w-100">詳細を見る</a>
                </div>
            </div>
        </div>
    '''

html_content += '''
    </div>
</div>
</body>
</html>
'''

with open(html_output_path, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"✅ HTMLファイルを出力しました: {html_output_path}")
