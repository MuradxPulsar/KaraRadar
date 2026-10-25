"""ip-api.com geolocation/ASN (passive, free)."""
import requests

TIMEOUT = 15

def lookup(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=TIMEOUT)
        r.raise_for_status()
        j = r.json()
    except Exception as e:
        return {"error": str(e)}
    if j.get("status") != "success":
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