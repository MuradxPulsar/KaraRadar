# KaraRadar

Passive OSINT anti-phishing tool for detecting domains impersonating Azerbaijani
brands. CLI + interactive menu. No API keys required by default.

## What it does
- Discovers candidate domains via certificate transparency (crt.sh, CertSpotter).
- Detects typosquatting, homoglyphs, IDN/punycode, added words, TLD swaps, hyphen merges.
- Enriches passively: RDAP, DNS, IP geolocation/ASN.
- Rule-based transparent scoring; three verdicts only.

## What it does NOT do
- No SMS/social phishing detection.
- No detection on legitimate-but-compromised sites.
- No non-brand-lookalike domains.
- Phase 1 never connects to target websites.

## False positives
Expected. Human review required. "Early warning, not complete protection."
Every report states: "Bu avtomatik ilkin qiymətləndirmədir, insan yoxlaması tələb olunur."

## Run
```
python main.py
python main.py --domains kapital-bank.az,azercell-login.xyz --lang az
python main.py --file domains.txt -o report.html
pytest
```

## Known limitations
- CT sources are rate-limited; failures are logged and skipped.
- ip-api.com free tier limits; RDAP coverage varies.
- pyyaml may be unavailable on Python 3.15; a minimal fallback parser is used.
- AI summary requires local Ollama (--ai).
- Brands list contains 112 Azerbaijani brand presets; extend via config/brands.yaml.

## CERT reporting
Report suspicious domains to info@cert.gov.az (template generated, never sent automatically).

## Ethics
Passive reconnaissance only. No exploitation, brute-force, or credential harvesting.

## Disclosure
AI-assisted development.

## License
MIT