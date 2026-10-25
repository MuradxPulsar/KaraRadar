"""RDAP enrichment (passive)."""
import requests, time

TIMEOUT = 15

def lookup(domain):
    url = f"https://rdap.org/domain/{domain}"
    try:
        r = requests.get(url, timeout=TIMEOUT, headers={"Accept": "application/json"})
        if r.status_code != 200:
            return None
        j = r.json()
    except Exception as e:
        return {"error": str(e)}
    info = {"domain": domain, "registrar": None, "created": None,
            "expires": None, "abuse_email": None, "events": []}
    for ev in j.get("events", []):
        action = ev.get("eventAction")
        date = ev.get("eventDate")
        info["events"].append({"action": action, "date": date})
        if action in ("registration", "registered"):
            info["created"] = date
        if action in ("expiration", "expiry"):
            info["expires"] = date
    for ent in j.get("entities", []):
        roles = ent.get("roles", [])
        vcard = ent.get("vcardArray", [])
        name = None
        if vcard and len(vcard) > 1:
            for item in vcard[1]:
                if item and item[0] == "fn":
                    name = item[3]
        if "registrar" in roles:
            info["registrar"] = name
        # abuse
        if "abuse" in roles:
            if vcard and len(vcard) > 1:
                for item in vcard[1]:
                    if item and item[0] == "email":
                        info["abuse_email"] = item[3]
    return info