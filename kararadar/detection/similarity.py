"""Similarity / lookalike detection helpers. Pure Python."""
import difflib
import re
import unicodedata

HOMOGLYPHS = {
    "0": "o", "o": "0", "1": "l", "l": "1", "i": "1",
    "a": "а",  # cyrillic a
    "а": "a",
    "e": "е",
    "е": "e",
    "o": "о",
    "о": "o",
    "p": "р",
    "р": "p",
    "c": "с",
    "с": "c",
    "x": "х",
    "х": "x",
    "rn": "m",
}

SUSPICIOUS_WORDS = ["login", "secure", "verify", "bonus", "az", "support", "update",
                    "bank", "hesab", "otp", "card"]

ABUSED_TLDS = {".top", ".xyz", ".buzz", ".click", ".live", ".rest", ".cam",
               ".gq", ".tk", ".ml", ".cf", ".ga"}


def levenshtein(a, b):
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost))
        prev = cur
    return prev[-1]


def normalize_domain(d):
    d = d.strip().lower().rstrip(".")
    # punycode decode attempt
    try:
        d = d.encode("ascii").decode("idna")
    except Exception:
        pass
    return d


def registered_name(domain):
    domain = normalize_domain(domain)
    parts = domain.split(".")
    if len(parts) < 2:
        return domain, ""
    # naive: last two labels
    return parts[-2], parts[-1]


def is_punycode(domain):
    return "xn--" in domain.lower()


def homoglyph_normalize(s):
    out = []
    for ch in s:
        out.append(HOMOGLYPHS.get(ch, ch))
    return "".join(out)


AZ_MAP = str.maketrans({
    "ə": "e", "ı": "i", "ş": "s", "ç": "c", "ö": "o",
    "ü": "u", "ğ": "g", "Ə": "E", "I": "i",
})

def az_normalize(s):
    return s.translate(AZ_MAP)


def detect(candidate, brand):
    """Compare candidate domain to a brand keyword/official domain.
    Returns list of (type, detail) tuples."""
    res = []
    cand = normalize_domain(candidate)
    c_name, c_tld = registered_name(cand)
    c_name = az_normalize(c_name)
    # brand may be domain or keyword
    b = brand.strip().lower()
    if "." in b:
        b_name, b_tld = registered_name(b)
    else:
        b_name, b_tld = b, ""
    b_name = az_normalize(b_name)

    # IDN / punycode
    if is_punycode(cand):
        res.append(("idn_punycode", "candidate uses punycode/IDN"))

    # homoglyph
    if homoglyph_normalize(c_name) == b_name and c_name != b_name:
        res.append(("homoglyph", f"confusable chars in '{c_name}' vs '{b_name}'"))

    # TLD swap
    if c_name == b_name and c_tld != b_tld and b_tld:
        res.append(("tld_swap", f"same name '{c_name}' but TLD differs ({c_tld} vs {b_tld})"))

    # levenshtein typosquat
    if b_name and c_name and c_name != b_name:
        dist = levenshtein(c_name, b_name)
        if 0 < dist <= 2:
            res.append(("typosquat", f"Levenshtein distance: {dist}"))

    # added word
    if b_name and b_name in c_name and c_name != b_name:
        extra = c_name.replace(b_name, "").strip("-_")
        if extra:
            res.append(("added_word", f"extra word '{extra}' added to brand name"))

    # hyphen merge
    if b_name and c_name.replace("-", "") == b_name.replace("-", "") and c_name != b_name:
        res.append(("hyphen_merge", "hyphen insertion/removal"))

    # transposition (adjacent char swap)
    if b_name and len(c_name) == len(b_name) and c_name != b_name:
        for i in range(len(c_name) - 1):
            swapped = c_name[:i] + c_name[i+1] + c_name[i] + c_name[i+2:]
            if swapped == b_name:
                res.append(("transposition", f"adjacent characters swapped at position {i}"))
                break

    # subdomain trick: brand appears in subdomain of unrelated registered domain
    parts = cand.split(".")
    if len(parts) > 2 and b_name and b_name in parts[:-2] and parts[-2] != b_name:
        res.append(("subdomain_trick", f"brand in subdomain of '{parts[-2]}.{parts[-1]}'"))

    # homoglyph via difflib close
    if not res and b_name and difflib.SequenceMatcher(None, c_name, b_name).ratio() > 0.85 and c_name != b_name:
        res.append(("fuzzy", "high textual similarity"))

    return res


def has_suspicious_word(domain):
    d = domain.lower()
    return [w for w in SUSPICIOUS_WORDS if w in d]


def abused_tld(domain):
    for t in ABUSED_TLDS:
        if domain.lower().endswith(t):
            return t
    return None


def generate_variants(name):
    """Generate simple lookalike variants for a brand name."""
    name = name.lower().strip()
    variants = set([name])
    # hyphen insert
    if "-" not in name:
        variants.add(name[:len(name)//2] + "-" + name[len(name)//2:])
    # homoglyph-ish swaps
    for a,b in (("o","0"),("l","1"),("i","1"),("a","4")):
        if a in name:
            variants.add(name.replace(a,b))
    # added suspicious word
    for w in ["login","secure","bank"]:
        variants.add(f"{name}-{w}")
    return sorted(variants)
