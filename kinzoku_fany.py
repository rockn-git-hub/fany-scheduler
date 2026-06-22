import time
import os
import json
import datetime
from zoneinfo import ZoneInfo
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

KEYWORD = "金属バット"
URL = f"https://ticket.fany.lol/search/event?keywords={KEYWORD}"
JSON_PATH = "previous_events.json"
HTML_PATH = "kinzoku_bat_events.html"
JST = ZoneInfo("Asia/Tokyo")


def log_time(label):
    """Emit timestamps to the GitHub Actions log for delay analysis."""
    print(f"[TIME] {label}: {datetime.datetime.now(JST).isoformat(timespec='seconds')}")


def init_driver():
    options = Options()
    options.add_argument("--headless")
    return webdriver.Chrome(options=options)


def expand_all(driver, wait):
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


def extract_event_list(driver):
    performances = driver.find_elements(By.CLASS_NAME, "fany_performanceListBox__outline")[0].find_elements(By.XPATH, "./div")
    result = []
    for perf in performances:
        try:
            title = perf.find_element(By.CLASS_NAME, "fany_performanceListBox__headerTitle").text.strip()
            date_text = perf.find_element(By.CLASS_NAME, "fany_performanceListBox__headerPerformanceDate").text.strip()
            date_str = date_text.split("(")[0].strip()
            event_date_str = datetime.datetime.strptime(date_str, "%Y/%m/%d").date().isoformat()
            venue = perf.find_element(By.CLASS_NAME, "fany_performanceListBox__headerVenue").text.strip()

            sale_status = "不明"
            for cls in ["fany_icon__sold", "fany_icon__soldout", "fany_icon__coming"]:
                found = perf.find_elements(By.CLASS_NAME, cls)
                if found:
                    sale_status = found[0].text.strip()
                    break

            link_elem = perf.find_element(By.CSS_SELECTOR, ".fany_g-ticketInfo a")
            detail_link = link_elem.get_attribute("href") if link_elem else None

            if "本公演" in title or not ("大阪府" in venue or "京都府" in venue):
                continue

            result.append({
                "title": title,
                "date": event_date_str,
                "date_text": date_text,
                "venue": venue,
                "sale_status": sale_status,
                "detail_link": detail_link,
            })
        except Exception as e:
            print(f"⚠️ スキップ（理由: {e}）")
    return result


def enrich_event_details(driver, events):
    for index, event in enumerate(events, start=1):
        prices = []
        open_start_time = ""

        if event["detail_link"]:
            log_time(f"detail_start {index}/{len(events)} {event['detail_link']}")
            try:
                driver.get(event["detail_link"])
                WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "g-sellItems_item")))

                try:
                    summary_box = driver.find_element(By.CLASS_NAME, "g-itemSet_summary")
                    for b in summary_box.find_elements(By.CLASS_NAME, "g-itemSet_body"):
                        text = b.text.strip()
                        if "開場" in text and "開演" in text:
                            open_start_time = text
                            break
                except:
                    open_start_time = ""

                ticket_sections = driver.find_elements(By.CLASS_NAME, "g-sellItems_item")
                for section in ticket_sections:
                    try:
                        seat_type = driver.execute_script("return arguments[0].textContent;", section.find_element(By.TAG_NAME, "dt")).strip()
                        ticket_divs = section.find_elements(By.CLASS_NAME, "g-sellItems_ticket")
                        for ticket_div in ticket_divs:
                            try:
                                ticket_type = driver.execute_script("return arguments[0].textContent;", ticket_div.find_element(By.CLASS_NAME, "g-sellItems_type")).strip()
                                price = driver.execute_script("return arguments[0].textContent;", ticket_div.find_element(By.CLASS_NAME, "g-sellItems_price")).strip()
                                prices.append(f"{seat_type}／{ticket_type}：{price}" if seat_type else f"{ticket_type}：{price}")
                            except Exception as e:
                                prices.append(f"{seat_type}／取得失敗：{e}")
                    except Exception as e:
                        prices.append(f"取得失敗：{e}")
            except Exception as e:
                prices.append(f"価格取得エラー: {e}")
            finally:
                log_time(f"detail_end {index}/{len(events)} {event['detail_link']}")
        else:
            prices.append("詳細リンクなし")

        event["prices"] = prices
        event["open_start_time"] = open_start_time


def mark_and_sort_new_events(events, prev_data):
    now = datetime.datetime.now(JST)
    now_id = now.strftime("%Y%m%d%H%M%S")
    threshold = now - datetime.timedelta(days=3)

    # 今回取得できたイベントのリンク一覧
    current_links = {e.get("detail_link") for e in events if e.get("detail_link")}

    # 残すべき旧データ（リンクがまだ生きてるやつだけ）
    valid_prev_data = [p for p in prev_data if p.get("detail_link") in current_links]

    # 新しいイベントの処理
    for e in events:
        match = next((p for p in valid_prev_data if p.get("detail_link") == e["detail_link"]), None)

        if match and "added_id" in match:
            try:
                added_dt = datetime.datetime.strptime(match["added_id"], "%Y%m%d%H%M%S").replace(tzinfo=JST)
                is_recent = added_dt >= threshold
            except ValueError:
                is_recent = False
            e["is_new"] = is_recent
            e["added_id"] = match["added_id"]
        elif match:
            e["is_new"] = True
            e["added_id"] = now_id
        else:
            e["is_new"] = True
            e["added_id"] = now_id

    # 並び順を調整（新着→追加順→開催日順）
    events.sort(key=lambda x: (
        x["is_new"],
        x.get("added_id", ""),
        x.get("date", "")
    ), reverse=True)

    return events


def generate_html(events, path):
    has_new = any(e.get("is_new") for e in events)
    title_text = "(new)金属バット公演一覧" if has_new else "金属バット公演一覧"
    heading_html = " {}金属バット公演一覧".format('<span class="badge bg-danger">新着あり</span> (new)' if has_new else "")

    html = f'''
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <title>{title_text}</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body class="bg-light">
<div class="container py-4">
    <h1 class="mb-4 text-center">{heading_html}</h1>
    <div class="row g-4">
'''

    for e in events:
        if "本公演" in e["title"]:
            continue
        title_with_new = f"{e['title']} <span class='badge bg-danger'>NEW</span>" if e.get("is_new") else e["title"]
        price_line = e["prices"][0] if e["prices"] else "情報なし"
        html += f'''
        <div class="col-md-6 col-lg-4">
            <div class="card shadow-sm h-100">
                <div class="card-body">
                    <h5 class="card-title">{title_with_new}</h5>
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

    html += '''
    </div>
</div>
</body>
</html>
'''
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"✅ HTMLファイルを出力しました: {path}")


def main():
    log_time("main_start")
    driver = init_driver()
    wait = WebDriverWait(driver, 10)
    driver.get(URL)
    log_time("top_page_loaded")

    expand_all(driver, wait)
    log_time("expand_all_done")
    events = extract_event_list(driver)
    print(f"[TIME] event_count: {len(events)}")
    log_time("event_list_extracted")
    enrich_event_details(driver, events)
    log_time("event_details_enriched")
    driver.quit()
    log_time("driver_quit")

    prev_data = []
    if os.path.exists(JSON_PATH):
        try:
            with open(JSON_PATH, "r", encoding="utf-8") as f:
                prev_data = json.load(f)
        except Exception as e:
            print(f"⚠️ 前回のJSON読み込みエラー: {e}")

    # 取得したイベントに、新着情報を付けたりソートしたりする
    events = mark_and_sort_new_events(events, prev_data)
    log_time("new_event_marking_done")

    # ✅ HTML は必ず生成（新着があるかどうかは中で判定される）
    generate_html(events, HTML_PATH)
    log_time("html_generated")

    # ✅ 新着がなければ JSON保存＆Git更新はスキップ
    if not any(e.get("is_new") for e in events):
        print("新規イベントはありませんでした。JSONの更新・コミットはスキップします。")
        log_time("main_end_no_new_events")
        return

    # ✅ 新着がある場合のみ JSONを更新
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print("✅ 新着イベントがあったため、JSONを更新しました。")
    log_time("main_end")


if __name__ == "__main__":
    main()
