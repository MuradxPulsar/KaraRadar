import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kararadar.detection import brandmatch, similarity
from kararadar.scoring import rules

def test_whitelist_gov():
    assert brandmatch.is_whitelisted("example.gov.az") is True
    assert brandmatch.is_whitelisted("foo.edu.az") is True

def test_typosquat_example_invalid():
    types = similarity.detect("kapital-bank.az", "kapitalbank")
    assert any(t[0] in ("typosquat", "added_word", "hyphen_merge") for t in types)

def test_idn_punycode():
    types = similarity.detect("xn--kapitalbank-9b.az", "kapitalbank")
    assert any(t[0] == "idn_punycode" for t in types)

def test_scoring_no_brand_neutral():
    res = rules.score_domain("example.invalid", rdap=None, dns=None, ip_list=[], brand_matches=[])
    assert res["brand_match"] is False
    # without infra signals, neutral
    assert res["verdict"] in ("neytral", "infrastruktur şübhəsi")

def test_scoring_brand_match():
    matches = [{"brand": "Kapital Bank", "types": [("typosquat", "d=1")]}]
    res = rules.score_domain("kapital-bank.az", rdap=None, dns=None, ip_list=[], brand_matches=matches)
    assert res["brand_match"] is True
    assert res["verdict"] == "brend təhliki şübhəsi"

def test_official_never_flagged():
    # official domain returns no matches
    ms = brandmatch.match("kapitalbank.az")
    assert ms == []