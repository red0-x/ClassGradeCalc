import csv, time, json, sys
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

repo_root = Path(__file__).resolve().parent.parent
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

from utils.webhandle import open_browser, cleanurls, get_enrolled_class_links, click_tab_if_present, scrape_assignment_page
from utils.injects import get_assignment_links_on_class


def bot():
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
        print(f"\n[!] Visiting class: {c.get('title') or c.get('aria_label')} -> {class_url}")

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
        print(assignments)
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
                    #assignments = get_assignments_from_student_work_page(driver) or []
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