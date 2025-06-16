import random
import subprocess
import time

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

URLS = [
    "https://www.popmart.com/ca/pop-now/set/171",
    "https://www.popmart.com/ca/pop-now/set/195",
    "https://www.popmart.com/ca/pop-now/set/67",
    "https://www.popmart.com/ca/pop-now/set/50",
]

IN_STOCK_TEXTS = {
    "ADD TO CART",
    "ADD TO BAG",
    "BUY NOW",
    "PICK ONE TO SHAKE",
}
OOS_TEXTS = {
    "NOTIFY ME WHEN AVAILABLE",
}

CHECK_INTERVAL = (2, 10)
ALERT_SOUND = "alert.mp3"

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--log-level=3")
ua = random.choice(
    [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)…",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)…",
    ]
)
options.add_argument(f"user-agent={ua}")
driver = webdriver.Chrome(options=options)


def alert_and_wait():
    proc = subprocess.Popen(
        ["mpg123", "--loop", "-1", ALERT_SOUND], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    input("▶ Product available! Press Enter to stop the alarm…")
    proc.terminate()


def check_one(url):
    driver.get(url)
    print(f"→ Checking {url}")

    try:
        # wait for full HTML load
        WebDriverWait(driver, 15).until(lambda d: d.execute_script("return document.readyState") == "complete")
        # wait for either an in-stock or out-of-stock button
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "//button[contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD TO BAG')"
                    + " or contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'ADD TO CART')"
                    + " or contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'BUY NOW')"
                    + " or contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'PICK ONE TO SHAKE')"
                    + " or contains(translate(., 'abcdefghijklmnopqrstuvwxyz','ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'NOTIFY ME')"
                    "]",
                )
            )
        )
    except TimeoutException:
        print(f"[-] Timeout waiting for render: {url}")
        return False

    # 3) gather texts
    texts = {
        el.text.strip().upper()
        for el in driver.find_elements(By.XPATH, "//button|//a|//div[@role='button']")
        if el.text and el.is_displayed()
    }

    # 4) decide
    if texts & IN_STOCK_TEXTS:
        label = next(iter(texts & IN_STOCK_TEXTS))
        print(f"[+] AVAILABLE ({label!r}): {url}")
        alert_and_wait()
        return True
    if texts & OOS_TEXTS:
        print(f"[-] Out of stock ({next(iter(texts & OOS_TEXTS))!r}): {url}")
        return False

    # 5) fallback if nothing matched
    print(f"[-] Unknown status, no matching labels found: {url}")
    return False


if __name__ == "__main__":
    print("Starting Labubu watcher ...")
    try:
        while True:
            for link in URLS:
                check_one(link)
                time.sleep(random.uniform(1, 3))
            wait = random.uniform(*CHECK_INTERVAL)
            print(f"…waiting {int(wait)}s before next sweep…\n")
            time.sleep(wait)
    except KeyboardInterrupt:
        print("Stopping watcher.")
    finally:
        driver.quit()
