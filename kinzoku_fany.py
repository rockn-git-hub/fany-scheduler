import os
import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import hashlib

# JSONファイルのパス
json_file_path = "last_kinzoku_bat_events.json"

# 前回の公演情報を読み込む
if os.path.exists(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as f:
        previous_events = json.load(f)
else:
    previous_events = []

# セットアップ
options = Options()
options.add_argument("--headless")  # デバッグ時は外す
driver = webdriver.Chrome(options=options)
driver.get("https://ticket.fany.lol/search/event?keywords=金属バット")

wait = WebDriverWait(driver, 10)

# 「もっと見る」を押し続ける
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

        # 公演日を取得
        date_text = perf.find_element(By.CLASS_NAME, "fany_performanceListBox__headerPerformanceDate").text.strip()
        date_str = date_text.split("(")[0].strip()
        event_date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()

        venue = perf.find_element(By.CLASS_NAME, "fany_performanceListBox__headerVenue").text.strip()

        # 販売ステータスを取得
        sale_status = "不明"
        for cls in ["fany_icon__sold", "fany_icon__soldout", "fany_icon__coming"]:
            found = perf.find_elements(By.CLASS_NAME, cls)
            if found:
                sale_status = found[0].text.strip()
                break

        # 詳細リンクを取得
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
            "date": event_date.isoformat(),
            "date_text": date_text,
            "venue": venue,
            "sale_status": sale_status,
            "detail_link": detail_link,
        })

    except Exception as e:
        print(f"⚠️ スキップ（理由: {e}）")
        continue

# 各イベントの価格情報を取得
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

                            ticket_type = driver.execute_script("return arguments[0].textContent;", ticket_type_el).strip()
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

# 前回のイベント情報と比較
def get_event_id(event):
    return hashlib.md5((event["title"] + event["date"] + event["venue"]).encode()).hexdigest()

previous_event_dict = {get_event_id(e): e for e in previous_events}

new_events =
::contentReference[oaicite:8]{index=8}
 
