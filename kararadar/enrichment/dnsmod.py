"""DNS enrichment (passive)."""
import dns.resolver

TIMEOUT = 8

def resolve(domain):
    out = {"A": [], "MX": [], "NS": [], "TXT": [], "SPF": None, "DMARC": None}
    resolver = dns.resolver.Resolver()
    resolver.lifetime = TIMEOUT
    for rtype, key in [("A", "A"), ("MX", "MX"), ("NS", "NS"), ("TXT", "TXT")]:
        try:
            ans = resolver.resolve(domain, rtype)
            for r in ans:
                s = str(r).strip()
                out[key].append(s)
                low = s.lower()
                if low.startswith('"v=spf1') or "v=spf1" in low:
                    out["SPF"] = s.strip('"')
        except Exception:
            pass
    # DMARC
    try:
        ans = resolver.resolve("_dmarc." + domain, "TXT")
        for r in ans:
            s = str(r).strip().strip('"')
            if "v=dmarc1" in s.lower():
                out["DMARC"] = s
    except Exception:
        pass
    return out