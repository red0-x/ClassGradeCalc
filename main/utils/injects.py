import sys
import time
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

def get_assignment_links_on_class(driver):
    # wait for either the classwork stream element or any expected anchors to appear
    try:
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script(
                "return !!(document.querySelector('div."+work+"') || document.querySelector('main') || "
                "document.querySelector('a[href*=\"/a/\"]') || document.querySelector('a[href*=\"/sp/\"]'))"
            )
        )
    except Exception:
        pass

    try:
        counts = driver.execute_script(
            "return { items: (document.querySelectorAll('[data-stream-item-id]').length||0), "
            "anchors: (document.querySelectorAll('a[href*=\"/a/\"], a[href*=\"/details\"], a[href*=\"/sp/\"]').length||0) };"
        )
        print(f"DEBUG: stream items={counts.get('items')} anchors={counts.get('anchors')}")
    except Exception as e:
        print("DEBUG: DOM probe failed:", e)

    try:
        for _ in range(6):
            driver.execute_script("const c=document.querySelector('div"+work+"')||document.querySelector('main')||document; if(c.scrollBy){c.scrollBy(0, window.innerHeight);} else {window.scrollBy(0, window.innerHeight);} ")
            time.sleep(0.25)
    except Exception:
        pass

    script = r"""(() => {
  const section = document.querySelector('section[aria-label="Classwork"]') || document.querySelector('main') || document;
  const anchors = Array.from(section.querySelectorAll('a'));
  const container = document.querySelector('div."""+work+r"""') || document.querySelector('main') || document;
  const items = Array.from(container.querySelectorAll('[data-stream-item-id]'));
  const results = [];
  const seenKeys = new Set();
  const seenSids = new Set();
  function textOrAria(el) { return (el && (el.textContent || el.getAttribute && el.getAttribute('aria-label')) || '').trim(); }
  function normalizeHref(el) {
    if (!el) return '';
    try {
      const attr = el.getAttribute && el.getAttribute('href');
      if (attr && attr.trim()) return attr.trim();
    } catch (e) {}
    try {
      if (el.href) return String(el.href);
    } catch (e) {}
    try {
      const dh = el.getAttribute && (el.getAttribute('data-href') || el.getAttribute('data-url'));
      if (dh && dh.trim()) return dh.trim();
    } catch (e) {}
    return '';
  }
  items.forEach((item, idx) => {
    try {
      const sid = item.getAttribute('data-stream-item-id') || ('si_' + idx);
      if (seenSids.has(sid)) return;
      seenSids.add(sid);
      const anchorsInItem = Array.from(item.querySelectorAll('a'));
      let foundHref = '';
      let foundAnchor = null;
      for (const a of anchorsInItem) {
        const h = normalizeHref(a);
        if (h) { foundHref = h; foundAnchor = a; break; }
        try {
          if (a.href && String(a.href).indexOf('http') === 0) { foundHref = String(a.href); foundAnchor = a; break; }
        } catch (e) {}
      }
      if (!foundHref) {
        const el = item.querySelector('[data-href], [data-url], [jsname="hSRGPd"]');
        if (el) {
          foundHref = normalizeHref(el) || (el.href ? String(el.href) : '') || '';
        }
      }
      const titleEl = item.querySelector('.YVvGBb') || item.querySelector('h1,h2,h3');
      const title = titleEl ? (titleEl.textContent || '').trim() : ((item.querySelector('[aria-label]') && item.querySelector('[aria-label]').getAttribute('aria-label')) || '').trim() || null;
      const nearby = (item.innerText || '').trim();
      const key = (foundHref || ('__nohref__' + sid)) + '|' + (title || '');
      if (seenKeys.has(key)) return;
      seenKeys.add(key);
      results.push({ href: foundHref || null, title: title || null, nearby: nearby || null, stream_id: sid });
    } catch (e) {
      console.log('[!] err process item', e);
    }
  });
  if (results.length === 0) {
    const anchors2 = Array.from(container.querySelectorAll('a, [data-href], [data-url], [jsname="hSRGPd"]'));
    const seen2 = new Set();
    anchors2.forEach((a, i) => {
      try {
        const href = normalizeHref(a) || (a.href ? String(a.href) : '');
        const title = (a.querySelector && (a.querySelector('.YVvGBb')?.textContent)) || a.getAttribute && a.getAttribute('aria-label') || a.textContent || '';
        const key = (href || ('__a_' + i)) + '|' + (title || '');
        if (!key || seen2.has(key)) return;
        seen2.add(key);
        results.push({ href: href || null, title: (title || null), nearby: (a.closest && a.closest('div')?.innerText) || (a.innerText || '').trim() || null, stream_id: null });
      } catch (e) {
      }
    });
  }
  return results;
})();"""

    try:
        raw = driver.execute_script(script) or []
    except Exception as e:
        print("JS extraction failed:", e)
        return []

    normalized = []
    base = "https://classroom.google.com"
    for item in (raw or []):
        href = item.get('href') or ''
        title = item.get('title') or item.get('title')
        nearby = item.get('nearby') or ''
        #convert and keep rel paths
        if href and href.startswith('https://') and href.startswith(base):
            # convert to rel path
            try:
                from urllib.parse import urlparse
                p = urlparse(href)
                href = p.path + (('?' + p.query) if p.query else '')
            except Exception:
                pass
        if href and href.startswith('/'):
            # keep rel href
            normalized.append({'href': href, 'title': title, 'nearby': nearby, 'stream_id': item.get('stream_id')})
        elif href:
            # full hreff
            normalized.append({'href': href, 'title': title, 'nearby': nearby, 'stream_id': item.get('stream_id')})
        else:
            normalized.append({'href': None, 'title': title, 'nearby': nearby, 'stream_id': item.get('stream_id')})
    return normalized