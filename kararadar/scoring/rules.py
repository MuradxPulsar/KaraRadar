"""Transparent rule-based scoring (no ML)."""
import datetime

SUSPICIOUS_WORDS = ["login", "secure", "verify", "bonus", "az", "support", "update"]
ABUSED_TLDS = {".top", ".xyz", ".buzz", ".click", ".live", ".rest", ".cam"}

try:
    import yaml
    HAS_YAML=True
except Exception:
    yaml=None
    HAS_YAML=False
import os

def _load_weights():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "config", "rules.yaml")
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f) if yaml else {}
        w = data.get("weights", {})
        if w:
            return w
    except Exception:
        pass
    return {}

_LOADED = _load_weights()

BRAND_WEIGHTS = {
    "typosquat": 30,
    "homoglyph": 40,
    "added_word": 20,
    "tld_swap": 25,
    "hyphen_merge": 15,
    "transposition": 25,
    "idn_punycode": 40,
    "fuzzy": 15,
}


def _age_days(created):
    if not created:
        return None
    try:
        dt = datetime.datetime.fromisoformat(str(created).replace("Z", "+00:00"))
        return (datetime.datetime.now(datetime.timezone.utc) - dt).days
    except Exception:
        # try date only
        try:
            dt = datetime.datetime.strptime(str(created)[:10], "%Y-%m-%d")
            return (datetime.datetime.utcnow() - dt).days
        except Exception:
            return None


def score_domain(domain, rdap=None, dns=None, ip_list=None, brand_matches=None):
    signals = []
    total = 0
    brand_match = bool(brand_matches)

    # domain age
    created = (rdap or {}).get("created") if rdap else None
    age = _age_days(created)
    if age is not None:
        if age < 30:
            signals.append(("domain age < 30 days", 35, f"registered {age} days ago"))
            total += 35
        elif age < 90:
            signals.append(("domain age < 90 days", 20, f"registered {age} days ago"))
            total += 20

    # brand similarity
    if brand_matches:
        for m in brand_matches:
            for typ, detail in m.get("types", []):
                w = BRAND_WEIGHTS.get(typ, 10)
                signals.append((f"brand lookalike ({typ})", w,
                                f"{m.get('brand')}: {detail}"))
                total += w

    # suspicious words
    sw = [w for w in SUSPICIOUS_WORDS if w in domain.lower()]
    # avoid double counting 'az' alone? keep simple
    if sw:
        w = min(10 * len(sw), 20)
        signals.append(("suspicious words", w, ", ".join(sw)))
        total += w

    # abused TLD
    for t in ABUSED_TLDS:
        if domain.lower().endswith(t):
            signals.append(("abused TLD", 25, t))
            total += 25
            break
    # email security (SPF/DMARC)
    dd = dns or {}
    has_dns = bool(dd.get("A") or dd.get("MX") or dd.get("NS") or dd.get("TXT"))
    if has_dns and not dd.get("SPF"):
        signals.append(("missing SPF", 8, "no SPF TXT record"))
        total += 8
    if has_dns and not dd.get("DMARC"):
        signals.append(("missing DMARC", 8, "no DMARC policy"))
        total += 8

    # ip/hosting anomalies
    for info in (ip_list or []):
        if isinstance(info, dict) and "error" not in info:
            if info.get("hosting"):
                signals.append(("hosting flag", 15, info.get("isp")))
                total += 15
            if info.get("proxy"):
                signals.append(("proxy flag", 15, info.get("isp")))
                total += 15
            country = info.get("country")
            if country and country.lower() not in ("azerbaijan",):
                signals.append(("foreign hosting", 10, country))
                total += 10

    # aggregation bonus
    registrar = (rdap or {}).get("registrar") if rdap else None
    if brand_match and age is not None and age < 90 and registrar:
        signals.append(("aggregation bonus", 20,
                        "new domain + brand lookalike + registrar present"))
        total += 20

    # verdict
    if brand_match:
        verdict = "brend təhliki şübhəsi"
    elif total >= 40:
        verdict = "infrastruktur şübhəsi"
    else:
        verdict = "neytral"

    return {"score": total, "verdict": verdict, "signals": [
        {"signal": s, "weight": w, "detail": d} for (s, w, d) in signals
    ], "brand_match": brand_match}
# apply yaml overrides if present
if _LOADED:
    BRAND_WEIGHTS.update({k: v for k, v in _LOADED.items() if k in BRAND_WEIGHTS or True})
