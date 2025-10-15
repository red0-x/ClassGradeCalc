from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.firefox_profile import FirefoxProfile
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import configparser
from pathlib import Path
import json
import csv

#firefox profile with logged in classroom account (firefox -p)
PROFILE_NAME = "dev-classroom"

#Google element class names 
clwaffle = "pYTkkf-Bz112c-RLmnJb"
work = "rVhh3b"
# Might need to figure out a way for the scraper to find these elements itself, if google changes them periodically.
# Want to add menu with colors later, updating the cycle so it goes Open webdriver -> checks if users logged into google/classroom account (continues o prompts login) & saving profile data 
# go to class home page -> inject class list retriever 
# in cli lets user pick the classes they want to scrape the grades from
# ex. Pick your classes to scrape:
# [1] Class 1
# [2] Class 2
# [3] Class 3
# Enter numbers separated by commas: 1,3
# then using the injected list it scrapes only those classes for assignemnts and grades.
# goes through for loop of the links -> opens that assignements page and clicks each element down the assignement div -> scrapes comments grade and due date -> goes back to class page -> next class
# saves all data to csv and json :) 

# maybe add a visualiszer using react later where you can paste your json/csv and it gives graphs and gpa? 


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
            "Firefox profile not found.\n"
            f"Looked for profile name: {PROFILE_NAME}\n"
            f"You can set FIREFOX_PROFILE_PATH environment variable to a full path to your profile.\n"
            f"Profiles available: {available}"
        )

    lock_file = Path(profile_path) / "lock"
    if lock_file.exists():
        print("Close other Firefox windows using that profile before running this script, or use a separate profile.")

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

def main():
    driver = open_browser()
    driver.get("https://classroom.google.com/")

    base = "https://classroom.google.com"


    time.sleep(1)
    WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    class_links = get_enrolled_class_links(driver) or []
    if not class_links:
        print("No enrolled class links found. Make sure the Classroom page is fully loaded and the 'Enrolled' section is visible.")
    class_links = cleanurls(class_links)
    print(f"Found {len(class_links)} class links")

    all_results = []
    for c in class_links:
        class_url = f"https://classroom.google.com{c.get('href')}"
        print(f"\n➡ Visiting class: {c.get('title') or c.get('aria_label')} -> {class_url}")

        try:
            driver.get(class_url)
            WebDriverWait(driver, 200).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            input("Press Enter to continue...") # Will change later for debugging

        except Exception as e:
            print("Failed to open class page:", e)
            continue

        try:
            click_tab_if_present(driver, "Classwork")
            time.sleep(1)
        except Exception:
            pass
        
        # Nee to click on elements (assignements for the specific class) inside of work div and retrieve grade, assignement name, due date, assignement date, comments, description (might be very long and need to be avoided) and docouments attached filename 
        assignments = get_assignment_links_on_class(driver) or []
        if not assignments:
            sp_links = driver.find_elements(By.XPATH, "//a[contains(@href,'/sp/')]")
            if sp_links:
                sp_href = sp_links[0].get_attribute('href')
                if sp_href and sp_href.startswith('/'):
                    sp_href = base + sp_href
                print(f"  Visiting student-work page: {sp_href}")
                try:
                    driver.get(sp_href)
                    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                    time.sleep(0.5)
                    assignments = get_assignments_from_student_work_page(driver) or []
                except Exception as e:
                    print("  Failed to open student-work page:", e)
        if not assignments:
            print("  No assignment links found on this class page (Classwork may be empty or use different markup).")
            #need to change element handing and parsing 
        print(f"  Found {len(assignments)} potential assignments")

        for a in assignments:
            href = a.get("href")
            if href and href.startswith("/"):
                href = base + href
            print(f"    - Opening assignment: {a.get('title') or href}")
            try:
                driver.get(href)
                WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(0.5)
            except Exception as e:
                print("      Failed to open assignment:", e)
                continue

            info = scrape_assignment_page(driver)
            info.update({
                "class_title": c.get("title") or c.get("aria_label"),
                "class_url": class_url,
                "assignment_url": href,
            })
            all_results.append(info)
    out_json = Path.cwd() / "grades.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"Wrote {len(all_results)} records to {out_json}")

    out_csv = Path.cwd() / "grades.csv"
    if all_results:
        keys = ["class_title", "class_url", "assignment_url", "title", "due", "score", "points_possible", "grade_text"]
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            for r in all_results:
                writer.writerow({k: r.get(k) for k in keys})
        print(f"Wrote CSV to {out_csv}")

    print("Done. Exiting and closing browser...")


def get_enrolled_class_links(driver):
    
    def extract_from_elements(elems):
        results = []
        seen = set()
        for a in elems:
            try:
                href = a.get_attribute('href') or ''
                data_id = a.get_attribute('data-id')
                if href.startswith('http'):
                    try:
                        from urllib.parse import urlparse
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


def get_assignment_links_on_class(driver):
    # inject into firefox page to get class links (returns list of links for classes)
    script = r"""
    (() => {
      const section = document.querySelector('section[aria-label="Classwork"]') || document.querySelector('main') || document;
      const anchors = Array.from(section.querySelectorAll('a'));
      const results = [];
      const seen = new Set();

      function textOrAria(el){ return (el.textContent||el.getAttribute('aria-label')||'').trim(); }

      anchors.forEach(a => {
        try{
          const href = a.getAttribute('href') || '';
          const txt = textOrAria(a);
          const titleEl = a.querySelector('h1,h2,h3') || a.querySelector('.GRvzhf.YVvGBb, .GRvzhf');
          let title = titleEl ? (titleEl.textContent||'').trim() : (txt || null);
          const nearby = a.closest('div')?.innerText || a.innerText || '';
          const key = (href||'') + '|' + (title||'');
          if (seen.has(key)) return;
          seen.add(key);
          results.push({ href: href, title: title, nearby: nearby });
        } catch(e) {
          // ignore individual failures
        }
      });
      return results;
    })();
    """

    try:
        raw = driver.execute_script(script) or []
    except Exception as e:
        print("JS extraction failed:", e)
        return []

    results = []
    for item in (raw or []):
        href = item.get('href') or ''
        title = item.get('title') or ''
        nearby = item.get('nearby') or ''
        results.append({'href': href, 'title': title, 'nearby': nearby})
    return results


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

    import re
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


def get_assignments_from_student_work_page(driver):
    """Extract assignments visible on a student-work (/sp/) listing page.

    Returns a list of dicts with href, title, due (raw text), and any visible score text.
    """
    script = r"""
    (() => {
      // Find rows/cards that look like student-work entries
      const rows = Array.from(document.querySelectorAll('a[href*="/c/"][href*="/sp/"] ~ div, div[role="listitem"], div[role="article"]'));
      const results = [];
      // fallback: all anchors containing '/sp/' or '/a/'
      const anchors = Array.from(document.querySelectorAll('a[href*="/sp/"], a[href*="/a/"]'));
      anchors.forEach(a => {
        const href = a.getAttribute('href') || '';
        const text = a.textContent || '';
        const title = a.querySelector('.GRvzhf.YVvGBb, .GRvzhf')?.textContent?.trim() || a.getAttribute('aria-label') || text.trim().slice(0,150);
        // look for date/grade text nearby
        const nearby = a.closest('div')?.innerText || a.innerText || '';
        const dueMatch = (nearby.match(/Due[:\s]*([A-Za-z0-9,\s:]+)$/mi) || [null, null])[1];
        const scoreMatch = (nearby.match(/([0-9]{1,3}(?:\.[0-9]+)?)\s*\/\s*([0-9]{1,3}(?:\.[0-9]+)?)/) || [null])[0];
        results.push({ href: href, title: title, due: dueMatch || null, score_text: scoreMatch || null });
      });
      return results;
    })();
    """
    try:
        res = driver.execute_script(script)
        normalized = []
        for r in (res or []):
            href = r.get('href') or ''
            if href.startswith('/'):
                href = 'https://classroom.google.com' + href
            normalized.append({'href': href, 'title': r.get('title'), 'due': r.get('due'), 'score_text': r.get('score_text')})
        return normalized
    except Exception as e:
        print('student-work extraction failed:', e)
        return []





if __name__ == "__main__":
    main()