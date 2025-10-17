// Payload for classroom link extraction
//[!] red0-x
(() => {
  const section = document.querySelector('section[aria-label="Classwork"]') || document.querySelector('main') || document;
  const anchors = Array.from(section.querySelectorAll('a'));
  const container = document.querySelector('div.rVhh3b') || document.querySelector('main') || document;
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
})();