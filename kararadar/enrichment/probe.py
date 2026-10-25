"""Safe HTTP probe (Phase 2-ish, only safe GET, no form submission)."""
import requests

def probe(url, timeout=10):
    try:
        r = requests.get(url, timeout=timeout, allow_redirects=True)
    except Exception as e:
        return {"error": str(e)}
    text = r.text or ""
    lower = text.lower()
    return {
        "status": r.status_code,
        "final_url": r.url,
        "redirects": [rr.url for rr in r.history],
        "has_password_field": 'type="password"' in lower or "type='password'" in lower,
        "has_login_form": "<form" in lower and ("login" in lower or "parol" in lower),
        "title": _title(text),
    }


def _title(html):
    import re
    m = re.search(r"<title>(.*?)</title>", html, re.I | re.S)
    return m.group(1).strip() if m else ""
