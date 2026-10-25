"""Match candidate domains against brands; whitelist logic."""
import os
import re

try:
    import yaml
    HAS_YAML = True
except Exception:
    HAS_YAML = False


def _simple_parse(path):
    # Minimal parser for brands.yaml subset
    brands = []
    current = None
    mode = None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            if line.strip() == "brands:":
                continue
            m = re.match(r"\s*-\s*name:\s*\"?(.*?)\"?\s*$", line)
            if m:
                if current:
                    brands.append(current)
                current = {"name": m.group(1), "keywords": [], "official_domains": []}
                mode = None
                continue
            m = re.match(r"\s*keywords:\s*\[(.*)\]\s*$", line)
            if m and current is not None:
                items = [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]
                current["keywords"] = items
                continue
            m = re.match(r"\s*official_domains:\s*\[(.*)\]\s*$", line)
            if m and current is not None:
                items = [x.strip().strip('"').strip("'") for x in m.group(1).split(",") if x.strip()]
                current["official_domains"] = items
                continue
    if current:
        brands.append(current)
    return {"brands": brands}


def load_brands(path=None):
    if path is None:
        # find config relative
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, "..", "config", "brands.yaml")
        path = os.path.normpath(path)
    if not os.path.exists(path):
        return []
    if HAS_YAML:
        try:
            with open(path, encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data.get("brands", []) if isinstance(data, dict) else (data or [])
        except Exception:
            pass
    data = _simple_parse(path)
    return data.get("brands", [])


def is_whitelisted(domain):
    d = domain.lower().rstrip(".")
    if d.endswith(".gov.az") or d.endswith(".edu.az") or d == "gov.az" or d == "edu.az":
        return True
    brands = load_brands()
    for b in brands:
        for od in b.get("official_domains", []):
            if d == od.lower() or d.endswith("." + od.lower()):
                return True
    return False


def match(candidate, brands=None):
    if brands is None:
        brands = load_brands()
    if is_whitelisted(candidate):
        return []
    from .similarity import detect
    matches = []
    for b in brands:
        targets = [b.get("name", "")] + b.get("keywords", []) + b.get("official_domains", [])
        all_types = []
        for t in targets:
            if not t:
                continue
            all_types += detect(candidate, t)
        # dedup by type
        seen = set()
        uniq = []
        for typ, detail in all_types:
            if typ in seen:
                continue
            seen.add(typ)
            uniq.append((typ, detail))
        if uniq:
            matches.append({"brand": b.get("name"), "types": uniq})
    return matches