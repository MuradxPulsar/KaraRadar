"""CertSpotter v1 (backup CT source)."""
import time
import requests

API = "https://api.certspotter.com/v1/issuances"
TIMEOUT = 15

def get_issuances(domain, limit=50):
    params = {
        "domain": domain,
        "include_subdomains": "true",
        "expand": "dns_names",
    }
    for attempt in range(3):
        try:
            r = requests.get(API, params=params, timeout=TIMEOUT)
            if r.status_code in (404,):
                return []
            r.raise_for_status()
            data = r.json()
            break
        except Exception as e:
            if attempt == 2:
                print(f"[w] certspotter failed: {e}")
                return []
            time.sleep(0.5 * (2 ** attempt))
    out = []
    for iss in (data or [])[:limit]:
        for dn in iss.get("dns_names") or [iss.get("common_name")]:
            if dn:
                out.append({"dns_name": dn, "issuer": iss.get("issuer", {}).get("organization_name")})
    return out