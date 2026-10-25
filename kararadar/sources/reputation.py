"""Optional reputation lookups (API keys required)."""
import os, requests

def virustotal(domain):
    key = os.getenv("VIRUSTOTAL_API_KEY")
    if not key:
        return None
    try:
        r = requests.get(f"https://www.virustotal.com/api/v3/domains/{domain}",
                         headers={"x-apikey": key}, timeout=15)
        if r.status_code != 200:
            return None
        j = r.json()
        stats = j.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        return stats
    except Exception:
        return None

def urlhaus(domain):
    try:
        r = requests.post("https://urlhaus-api.abuse.ch/v1/host/", data={"host": domain}, timeout=15)
        if r.status_code != 200:
            return None
        return r.json()
    except Exception:
        return None
