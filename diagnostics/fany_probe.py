"""GitHub環境でのFANY取得失敗の診断用処理"""

import json
from pathlib import Path
import sys
import traceback
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from kinzoku_fany import URL, expand_all, extract_event_list, init_driver

OUTPUT = Path("fany-diagnostics")
OUTPUT.mkdir(exist_ok=True)
ENCODED_URL = quote(URL, safe=":/?=&%")


def report(label, data):
    """診断情報の標準出力とJSON保存"""
    print(label + " " + json.dumps(data, ensure_ascii=False), flush=True)
    (OUTPUT / (label + ".json")).write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def snapshot(driver, label):
    """ブラウザーの表示内容と要素数の保存"""
    report(label, {
        "url": driver.current_url,
        "title": driver.title,
        "ready_state": driver.execute_script("return document.readyState"),
        "list_count": len(driver.find_elements(By.CLASS_NAME, "fany_performanceListBox__outline")),
        "title_count": len(driver.find_elements(By.CLASS_NAME, "fany_performanceListBox__headerTitle")),
        "more_count": len(driver.find_elements(By.CSS_SELECTOR, ".more-btn button")),
        "body_text": driver.find_element(By.TAG_NAME, "body").text[:5000],
    })
    (OUTPUT / (label + ".html")).write_text(driver.page_source, encoding="utf-8")
    driver.save_screenshot(str(OUTPUT / (label + ".png")))


def probe_http():
    """同じ実行環境からの通常HTTP取得の比較"""
    try:
        response = urlopen(Request(ENCODED_URL), timeout=30)
    except HTTPError as error:
        response = error
    with response:
        text = response.read().decode("utf-8", errors="replace")
        (OUTPUT / "http.html").write_text(text, encoding="utf-8")
        report("http", {
            "status": response.status,
            "url": response.url,
            "content_type": response.headers.get("Content-Type"),
            "server": response.headers.get("Server"),
            "list_found": "fany_performanceListBox__outline" in text,
            "length": len(text),
            "body_prefix": text[:1200],
        })


def probe_original():
    """本番と同じブラウザー初期化と公演取得処理の再現"""
    driver = init_driver()
    try:
        report("versions", driver.capabilities)
        driver.set_page_load_timeout(45)
        driver.get(URL)
        snapshot(driver, "original_loaded")
        expand_all(driver, WebDriverWait(driver, 10))
        snapshot(driver, "original_expanded")
        try:
            events = extract_event_list(driver)
            report("extraction", {"count": len(events)})
        except Exception:
            report("extraction_error", {"traceback": traceback.format_exc()})
        if not driver.find_elements(By.CLASS_NAME, "fany_performanceListBox__outline"):
            try:
                WebDriverWait(driver, 30).until(
                    lambda browser: browser.find_elements(By.CLASS_NAME, "fany_performanceListBox__outline")
                )
            except Exception:
                report("extended_wait", {"error": traceback.format_exc()})
            snapshot(driver, "original_after_wait")
    finally:
        driver.quit()


def probe_network():
    """URLを明示的にエンコードしたブラウザー通信の診断"""
    options = Options()
    options.add_argument("--headless")
    options.set_capability("goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"})
    driver = webdriver.Chrome(options=options)
    try:
        driver.set_page_load_timeout(45)
        driver.get(ENCODED_URL)
        snapshot(driver, "network_loaded")
        entries = []
        for item in driver.get_log("performance"):
            message = json.loads(item["message"])["message"]
            if message["method"] in ("Network.loadingFailed", "Network.responseReceived"):
                params = message["params"]
                response = params.get("response", {})
                entries.append({
                    "method": message["method"],
                    "type": params.get("type"),
                    "url": response.get("url"),
                    "status": response.get("status"),
                    "error": params.get("errorText"),
                })
        report("network", entries)
        report("browser_log", driver.get_log("browser"))
    finally:
        driver.quit()


def main():
    """各診断の独立実行と失敗内容の保存"""
    for probe in (probe_http, probe_original, probe_network):
        try:
            probe()
        except Exception:
            report(probe.__name__ + "_error", {"traceback": traceback.format_exc()})


if __name__ == "__main__":
    main()
