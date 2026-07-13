import time
from playwright.sync_api import sync_playwright

BASE = "http://127.0.0.1:8001/"
PAGES = ["page-list", "page-examples", "page-test", "page-grammar", "page-gramword", "page-gramtest"]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)

    page = browser.new_page(viewport={"width": 375, "height": 812})
    page.goto(BASE, wait_until="networkidle")
    time.sleep(0.8)
    for pid in PAGES:
        count = page.eval_on_selector_all(f"#{pid} .mobile-page-switcher .chip", "els => els.length")
        assert count == 3, f"FAIL: {pid} has {count} switcher buttons, expected 3"
    print("PASS: all 6 pages have a 3-button switcher in the DOM")

    visible = page.eval_on_selector("#page-list .mobile-page-switcher", "el => getComputedStyle(el).display")
    assert visible != "none", "FAIL: switcher should be visible at 375px"
    print("PASS: switcher visible at 375px")
    page.close()

    page2 = browser.new_page(viewport={"width": 768, "height": 1024})
    page2.goto(BASE, wait_until="networkidle")
    time.sleep(0.8)
    hidden = page2.eval_on_selector("#page-list .mobile-page-switcher", "el => getComputedStyle(el).display")
    assert hidden == "none", "FAIL: switcher should be hidden at 768px"
    print("PASS: switcher hidden at 768px")
    page2.close()

    browser.close()
