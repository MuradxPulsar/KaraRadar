"""crt.sh certificate transparency source (passive)."""
import time
import requests

CRTSH = "https://crt.sh/"
TIMEOUT = 10

def _get(params):
    for attempt in range(2):
        try:
            r = requests.get(CRTSH, params=params, timeout=TIMEOUT)
            if r.status_code in (400,404):
                return None
            if r.status_code >= 500:
                raise RuntimeError(f"crt.sh HTTP {r.status_code}")
            r.raise_for_status()
            return r.json()
        except Exception:
            if attempt == 1:
                return None
            time.sleep(0.5 * (2 ** attempt))

def search_keyword(keyword, limit=200, include_expired=False):
    """Search CT logs for a brand keyword. Returns set of domains."""
    kw = "".join(str(keyword).split()).lower()
    params = {"q": f"%{kw}%", "output": "json"}
    if not include_expired:
        params["exclude"] = "expired"
    try:
        data = _get(params)
    except Exception as e:
        print(f"[w] crt.sh search failed: {e}")
        return []
    if data is None:
        return []
    if data is None:
        return []
    domains = set()
    for entry in data or []:
        for field in ("common_name", "name_value"):
            val = entry.get(field)
            if not val:
                continue
            for line in str(val).splitlines():
                line = line.strip().lower().lstrip("*.")
                if line and "." in line:
                    domains.add(line)
    return list(domains)[:limit]

def search_domain(domain, limit=100, include_expired=False, q_format="domain"):
    """Return certificates for an exact domain or its subdomains."""
    q = domain if q_format == "domain" else f"%.{domain}"
    params = {"q": q, "output": "json"}
    if not include_expired:
        params["exclude"] = "expired"
    try:
        data = _get(params)
    except Exception as e:
        print(f"[w] crt.sh search failed: {e}")
        return []
    if data is None:
        return []
    if data is None:
        return []
    out = []
    for entry in (data or [])[:limit]:
        entry_id = entry.get("id") or entry.get("certificate_id")
        out.append({
            "common_name": entry.get("common_name"),
            "issuer_name": entry.get("issuer_name"),
            "not_before": entry.get("not_before"),
            "not_after": entry.get("not_after"),
            "serial_number": entry.get("serial_number"),
            "id": entry_id,
            "crt_sh_url": f"https://crt.sh/?id={entry_id}" if entry_id else None,
        })
    return out


def enumerate_subdomains(domain, limit=500):
    """Return unique subdomains for a domain discovered via CT logs (skill suggestion)."""
    params = {"q": f"%.{domain}", "output": "json", "exclude": "expired"}
    try:
        data = _get(params)
    except Exception:
        return []
    if data is None:
        return []
    subs = set()
    for entry in (data or []):
        for field in ("common_name", "name_value"):
            val = entry.get(field)
            if not val:
                continue
            for line in str(val).splitlines():
                name = line.strip().lower().lstrip("*.")
                if name and (name == domain or name.endswith(f".{domain}")):
                    subs.add(name)
    return sorted(subs)[:limit]