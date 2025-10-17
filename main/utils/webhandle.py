import sys
import os
import configparser
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from main import PROFILE_NAME, clwaffle, work

#selenium imports
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium import webdriver
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from urllib.parse import urlparse

def find_firefox_profile(profile_name: str) -> str | None:
   
    firefox_dir = Path.home() / ".mozilla" / "firefox"
    profiles_ini = firefox_dir / "profiles.ini"

    if not firefox_dir.exists():
        return None

    if profiles_ini.exists():
        parser = configparser.ConfigParser()
        parser.read(profiles_ini)
        for section in parser.sections():
            if not section.lower().startswith("profile"):
                continue
            name = parser.get(section, "Name", fallback=None)
            path = parser.get(section, "Path", fallback=None)
            is_relative = parser.get(section, "IsRelative", fallback="1")
            if name == profile_name and path:
                if is_relative == "1":
                    return str((firefox_dir / path).resolve())
                else:
                    return str(Path(path).resolve())

    for child in firefox_dir.iterdir():
        if child.is_dir() and child.name.endswith(f".{profile_name}"):
            return str(child.resolve())

    return None


def open_browser():
    profile_path = find_firefox_profile(PROFILE_NAME)

    if profile_path is None:
        env_path = os.environ.get("FIREFOX_PROFILE_PATH")
        if env_path:
            profile_path = os.path.expanduser(env_path)

    if not profile_path or not os.path.isdir(profile_path):
        available = []
        firefox_dir = Path.home() / ".mozilla" / "firefox"
        if firefox_dir.exists():
            for d in firefox_dir.iterdir():
                if d.is_dir():
                    available.append(d.name)

        raise FileNotFoundError(
            "[!] Couldnt find firefox profile\n"
            f"Looked for profile name: {PROFILE_NAME}\n"
            f"(set FIREFOX_PROFILE_PATH environment variable to a full path to your profile.)\n"
            f"Profiles available: {available}"
        )

    lock_file = Path(profile_path) / "lock"
    if lock_file.exists():
        print("close other firefox windows while using")

    profile = FirefoxProfile(profile_path)

    options = Options()
    options.set_preference("dom.webdriver.enabled", False)
    options.profile = profile

    driver = webdriver.Firefox(options=options)
    return driver

def cleanurls(urls):
    cleaned = []
    for url in urls:
        href = url.get("href")

        if href.endswith("default"):
            cleaned.append(url)
    return cleaned


def get_enrolled_class_links(driver):
    # Adapted from older code: extract class links from Classroom landing page
    def extract_from_elements(elems):
        results = []
        seen = set()
        for a in elems:
            try:
                href = a.get_attribute('href') or ''
                data_id = a.get_attribute('data-id')
                if href.startswith('http'):
                    try:
                        p = urlparse(href)
                        href_norm = p.path + (('?' + p.query) if p.query else '')
                    except Exception:
                        href_norm = href
                else:
                    href_norm = href
                if not data_id and not href_norm.startswith('/c/'):
                    continue
                title = None
                subtitle = None
                try:
                    title_el = a.find_element(By.CSS_SELECTOR, '.GRvzhf.YVvGBb, .GRvzhf')
                    title = title_el.text.strip()
                except Exception:
                    pass
                try:
                    subtitle_el = a.find_element(By.CSS_SELECTOR, '.DWJNgb.YVvGBb, .DWJNgb')
                    subtitle = subtitle_el.text.strip()
                except Exception:
                    pass
                aria = a.get_attribute('aria-label')
                key = (href_norm or '') + '|' + (data_id or '')
                if key in seen:
                    continue
                seen.add(key)
                results.append({ 'href': href_norm, 'data_id': data_id, 'aria_label': aria, 'title': title, 'subtitle': subtitle })
            except Exception:
                continue
        return results

    max_attempts = 8
    pause = 1.0
    for attempt in range(max_attempts):
        try:
            elems = driver.find_elements(By.CSS_SELECTOR, 'a[data-id], a[href^="/c/"]')
        except Exception:
            elems = []
        results = extract_from_elements(elems)
        if results:
            return results
        try:
            driver.execute_script('window.scrollBy(0, window.innerHeight);')
        except Exception:
            pass
        time.sleep(pause)

    try:
        now = int(time.time())
        screenshot = Path.cwd() / f'no_enrolled_{now}.png'
        htmlfile = Path.cwd() / f'no_enrolled_{now}.html'
        try:
            driver.save_screenshot(str(screenshot))
        except Exception:
            pass
        try:
            with open(htmlfile, 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
        except Exception:
            pass
        print(f"No enrolled class links found after {max_attempts} attempts. Saved screenshot: {screenshot} and page HTML: {htmlfile}")
    except Exception:
        pass
    return []


def click_tab_if_present(driver, tab_text):
    try:
        xpath = ("//a[.//div[contains(normalize-space(.), '{0}')]] | //button[.//div[contains(normalize-space(.), '{0}')]] | //a[contains(normalize-space(.), '{0}')]"
               ).format(tab_text)
        el = driver.find_element(By.XPATH, xpath)
        el.click()
        WebDriverWait(driver, 10).until(EC.staleness_of(el))
    except Exception:
        return


def scrape_assignment_page(driver):

    time.sleep(0.5)
    try:
        title = driver.execute_script("return document.querySelector('h1')?.textContent?.trim() || document.title || null;")
    except Exception:
        title = None

    try:
        body_text = driver.execute_script("return document.body.innerText || '';") or ""
    except Exception:
        body_text = ""

    grade_text = None
    score = None
    points_possible = None

    patterns = [
        re.compile(r"Your grade[:\s]*([0-9]+(?:\.[0-9]+)?)(?:\s*/\s*([0-9]+(?:\.[0-9]+)?))?", re.I),
        re.compile(r"Score[:\s]*([0-9]+(?:\.[0-9]+)?)", re.I),
        re.compile(r"([0-9]{1,3}(?:\.[0-9]+)?)\s*/\s*([0-9]{1,3}(?:\.[0-9]+)?)"),
    ]
    for p in patterns:
        m = p.search(body_text)
        if m:
            grade_text = m.group(0)
            try:
                if m.lastindex >= 1:
                    score = float(m.group(1))
                if m.lastindex >= 2 and m.group(2) is not None:
                    points_possible = float(m.group(2))
            except Exception:
                pass
            break

    if not grade_text:
        if re.search(r"not graded|ungraded|no grade", body_text, re.I):
            grade_text = "Not graded"

    due = None
    m = re.search(r"Due[:\s]*([A-Za-z0-9,\s:]+)" , body_text)
    if m:
        due = m.group(1).strip()

    return {
        "title": title,
        "due": due,
        "score": score,
        "points_possible": points_possible,
        "grade_text": grade_text,
    }
