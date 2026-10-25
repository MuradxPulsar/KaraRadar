"""ip-api.com geolocation/ASN (passive, free)."""
import requests
from kararadar.core.radar_anim import log_checked, with_radar

TIMEOUT = 15

@with_radar("IP info")
def lookup(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=TIMEOUT)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        return {"error": str(e)}
    if j.get("status") != "success":
        log_checked(f"✖ IP {ip} → {j.get('message')}")
        return {"error": j.get("message", "fail")}
    return {
        "ip": ip,
        "country": j.get("country"),
        "isp": j.get("isp"),
        "org": j.get("org"),
        "asn": j.get("as"),
        "hosting": j.get("hosting", False),
        "proxy": j.get("proxy", False),
        "mobile": j.get("mobile", False),
    }
    log_checked(f"✔ IP {ip} → {j.get('country')}")
    # log handled by caller maybe