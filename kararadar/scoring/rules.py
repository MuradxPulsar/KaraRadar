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

_DEFAULTS = {
    "typosquat": 30,
    "homoglyph": 40,
    "added_word": 20,
    "tld_swap": 25,
    "hyphen_merge": 15,
    "transposition": 25,
    "idn_punycode": 40,
    "fuzzy": 15,
    "domain_age_30": 35,
    "domain_age_90": 20,
    "suspicious_word": 10,
    "abused_tld": 25,
    "missing_spf": 8,
    "missing_dmarc": 8,
    "hosting_flag": 15,
    "proxy_flag": 15,
    "foreign_hosting": 10,
    "aggregation_bonus": 20,
}

WEIGHTS = dict(_DEFAULTS)
WEIGHTS.update({k: v for k, v in _LOADED.items() if k in _DEFAULTS})

def W(key, default=None):
    return WEIGHTS.get(key, default if default is not None else _DEFAULTS.get(key, 0))

BRAND_WEIGHTS = {k: WEIGHTS.get(k, v) for k, v in _DEFAULTS.items()
                 if k in ("typosquat","homoglyph","added_word","tld_swap",
                          "hyphen_merge","transposition","idn_punycode","fuzzy")}


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
            w = W("domain_age_30")
            signals.append(("domain age < 30 days", w, f"registered {age} days ago"))
            total += w
        elif age < 90:
            w = W("domain_age_90")
            signals.append(("domain age < 90 days", w, f"registered {age} days ago"))
            total += w

    # brand similarity
    if brand_matches:
        for m in brand_matches:
            for typ, detail in m.get("types", []):
                w = W(typ, 10)
                signals.append((f"brand lookalike ({typ})", w,
                                f"{m.get('brand')}: {detail}"))
                total += w

    # suspicious words
    sw = [w for w in SUSPICIOUS_WORDS if w in domain.lower()]
    # avoid double counting 'az' alone? keep simple
    if sw:
        w = min(W("suspicious_word", 10) * len(sw), 2 * W("suspicious_word", 10))
        signals.append(("suspicious words", w, ", ".join(sw)))
        total += w

    # abused TLD
    for t in ABUSED_TLDS:
        if domain.lower().endswith(t):
            w = W("abused_tld", 25)
            signals.append(("abused TLD", w, t))
            total += w
            break
    # email security (SPF/DMARC)
    dd = dns or {}
    has_dns = bool(dd.get("A") or dd.get("MX") or dd.get("NS") or dd.get("TXT"))
    if has_dns and not dd.get("SPF"):
        w = W("missing_spf", 8)
        signals.append(("missing SPF", w, "no SPF TXT record"))
        total += w
    if has_dns and not dd.get("DMARC"):
        w = W("missing_dmarc", 8)
        signals.append(("missing DMARC", w, "no DMARC policy"))
        total += w

    # ip/hosting anomalies
    for info in (ip_list or []):
        if isinstance(info, dict) and "error" not in info:
            if info.get("hosting"):
                w = W("hosting_flag", 15)
                signals.append(("hosting flag", w, info.get("isp")))
                total += w
            if info.get("proxy"):
                w = W("proxy_flag", 15)
                signals.append(("proxy flag", w, info.get("isp")))
                total += w
            country = info.get("country")
            if country and country.lower() not in ("azerbaijan",):
                w = W("foreign_hosting", 10)
                signals.append(("foreign hosting", w, country))
                total += w

    # aggregation bonus
    registrar = (rdap or {}).get("registrar") if rdap else None
    if brand_match and age is not None and age < 90 and registrar:
        w = W("aggregation_bonus", 20)
        signals.append(("aggregation bonus", w,
                        "new domain + brand lookalike + registrar present"))
        total += w

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
