Build a complete Python CLI OSINT anti-phishing tool named "KaraRadar" from

scratch, designed to detect domains impersonating Azerbaijani brands using

ONLY passive reconnaissance. The tool must run on Windows 11 CMD, require

NO API keys by default, use only pure-Python dependencies, and be ready to

publish on GitHub under MIT license.



== PROJECT STRUCTURE ==

kararadar/

├── kararadar/

│   ├── \_\_init\_\_.py

│   ├── main.py            # CLI entry point + interactive menu

│   ├── core/

│   │   ├── \_\_init\_\_.py

│   │   ├── colors.py      # colorama: green \[+], red \[!], yellow \[i], cyan headers

│   │   ├── spinner.py     # thread-based progress spinner

│   │   ├── cache.py       # SQLite cache with TTL for domains, RDAP, IP lookups

│   │   └── report.py      # export TXT, JSON, CSV, HTML, Markdown (AZ + EN)

│   ├── sources/

│   │   ├── \_\_init\_\_.py

│   │   ├── crtsh.py       # crt.sh JSON API

│   │   └── certspotter.py # CertSpotter v1 API (backup source)

│   ├── detection/

│   │   ├── \_\_init\_\_.py

│   │   ├── similarity.py  # Levenshtein (difflib), homoglyph (l/1, o/0, rn/m,

│   │   │                  # Cyrillic/Latin), IDN/punycode, added-word, TLD-swap,

│   │   │                  # hyphen-merge detection. Each match records its TYPE.

│   │   └── brandmatch.py  # match candidate domain against all brands+keywords

│   ├── enrichment/

│   │   ├── \_\_init\_\_.py

│   │   ├── rdap.py        # registration date, registrar, abuse email

│   │   ├── dnsmod.py      # dnspython: A, MX, NS records

│   │   └── ipinfo.py      # ip-api.com free JSON (country, ISP, ASN, proxy/hosting flags)

│   ├── scoring/

│   │   ├── \_\_init\_\_.py

│   │   └── rules.py       # transparent rule-based scoring (NO ML)

│   ├── reports/

│   │   ├── \_\_init\_\_.py

│   │   ├── html\_gen.py    # clean HTML report + simple SVG relation graph

│   │   │                  # (shared IP/registrar/cert connections)

│   │   └── templates.py   # AZ + EN strings; CERT email template (info@cert.gov.az)

│   └── ai/

│       └── ollama\_sum.py  # optional: local Ollama summary, OFF by default, --ai flag

├── config/

│   └── brands.yaml        # 112 Azerbaijani brand presets (I will paste it below)

├── tests/

│   └── test\_detection.py  # offline tests: similarity on example.invalid domains

├── setup.py, requirements.txt, README.md, LICENSE (MIT), .gitignore

└── .github/workflows/daily.yml  # GitHub Actions: daily run, stats-only to GitHub Pages



== TECHNICAL REQUIREMENTS ==

\- Python 3.12-3.13 (NOT 3.15 — dependency wheels may be missing)

\- asyncio with per-source rate limiting, exponential-backoff retry, 15s timeouts

\- If one source fails/timeouts, continue with the others silently (log warning)

\- Pure-Python deps only: requests, dnspython, pyyaml, colorama, rich (optional)

\- ASCII banner via pyfiglet "KaraRadar" + crow ASCII art

\- Interactive menu (python main.py):

&#x20; 1. Brand monitoring (default preset brands, CT discovery mode)

&#x20; 2. Analyze my own domains (user types domain1,domain2 or a .txt file path)

&#x20; 3. Manage brands (add / remove / list — persists to brands.yaml)

&#x20; 4. Settings (language AZ/EN, report format)

&#x20; 5. Exit

\- CLI flags mirror the menu: --domains, --file, --add-brand, --remove-brand,

&#x20; --list-brands, --since N (only domains first seen in last N days), --ai,

&#x20; --json, --lang az|en, -o output file



== BRAND \& DOMAIN RULES ==

\- brands.yaml contains: name, keywords\[], official\_domains\[] (WHITELIST).

\- ANY domain in official\_domains, any \*.gov.az, and any \*.edu.az is

&#x20; AUTO-WHITELISTED and never flagged (note this in output).

\- MODE A (monitor): search CT logs with keyword pattern "%%keyword%%" using

&#x20; requests params (let requests URL-encode, do NOT manually write %25 —

&#x20; that causes HTTP 400 on crt.sh).

\- MODE B (user domains): for each user-supplied domain run full analysis:

&#x20; a) similarity check against ALL preset brands (e.g. "kapital-bank.az" is

&#x20;    close to kapitalbank → signal "brand lookalike, Levenshtein distance: 1")

&#x20; b) if NO brand match: mark "Brend uyğunluğu: tapılmadı" (NEUTRAL — never

&#x20;    auto-suspicious) and score purely on infrastructure signals

&#x20; c) output card per domain: suspicion level + human-readable "NİYƏ?" list

&#x20;    with each signal and its weight + advice ("rəsmi kanalla yoxla" etc.)



== SCORING (rule-based, transparent, NO ML) ==

Signals (each with explicit weight, shown in report):

\- domain age < 30 days (strong), < 90 days (medium)

\- brand keyword similarity (type: typosquat/homoglyph/added-word/TLD-swap)

\- suspicious words: login, secure, verify, bonus, az, support, update

\- abused TLDs (.top, .xyz, .buzz, .click, .live, .rest, .cam)

\- hosting country / ASN anomalies; proxy/hosting flags from ip-api

\- AGGREGATION BONUS: same registrar + new domain + brand lookalike together

&#x20; = higher than the sum of individual scores (explicit combined rule)

\- NO brand match = neutral (0 brand points)

Three verdicts ONLY: "brend təhliki şübhəsi" / "infrastruktur şübhəsi" /

"neytral". NEVER write "zərərli/malicious". Every report includes the note:

"Bu avtomatik ilkin qiymətləndirmədir, insan yoxlaması tələb olunur."



== ENRICHMENT (passive only — Phase 1 MUST NOT connect to target websites) ==

RDAP (rdap.org or registrar RDAP), DNS records, ip-api.com per-IP geolocation

\+ ASN + proxy/hosting flags, certificate issuer/dates. Cache everything in

SQLite with TTL to respect rate limits.



== REPORTS ==

\- Formats: JSON, CSV, TXT, HTML (clean responsive design), Markdown

\- Languages: Azerbaijani AND English (reports/templates.py holds both)

\- HTML includes simple SVG relation graph linking domains by shared

&#x20; IP / registrar / certificate

\- Include ready-to-send CERT notification email template (info@cert.gov.az)

&#x20; — generate the TEXT only, never send anything

\- Daily GitHub Actions workflow publishes ONLY aggregate statistics

&#x20; (counts, trends) to GitHub Pages — individual suspicious domain names are

&#x20; NEVER made public before CERT notification



== OPTIONAL PHASE 2 (default OFF) ==

\--enable-sandbox-view flag: Playwright headless inside Docker ONLY —

screenshot, password/card field presence, form action URL, redirects,

iframe/script list. RULES: never type into forms, never click buttons,

never upload files, never port-scan, never vulnerability-test. Read-only.

Show warning before use.



== TESTS (offline, no network) ==

\- similarity detection on example.invalid / test.invalid domains

\- whitelist check: \*.gov.az and official\_domains are never flagged

\- scoring: verify brand-match vs no-brand paths

Run: pytest — all green required.



== README MUST CONTAIN ==

\- What the tool DOES and DOES NOT do (no SMS/social phishing detection, no

&#x20; detection on legitimate-but-hacked sites, no non-brand-lookalike domains)

\- False positives are expected; human review required; "early warning, not

&#x20; complete protection"

\- References for all sources used

\- Disclosure: "AI-assisted development"

\- Ethics + how to report to CERT (info@cert.gov.az)



== SAFETY (non-negotiable) ==

\- Phase 1: ZERO connections to target websites

\- No exploitation, no brute-force, no credential harvesting features

\- Every report states accuracy limitations



== ACCEPTANCE CRITERIA ==

1\. python main.py shows banner + menu

2\. Real crt.sh query works for at least one brand

3\. Uydurma test domenlərində (example.invalid tipli) bənzərlik aşkarlanır,

&#x20;  rəsmi domenlər heç vaxt şübhəli sayılmır

4\. HTML hesabat AZ və EN yaranır

5\. pytest passes, README reflects reality

6\. HONESTY REQUIREMENT: final report must explicitly state what works, what

&#x20;  is untested, which sources are rate-limited, and known false-positive

&#x20;  cases. NEVER claim features that were not executed and verified.



IMPORTANT: build module by module. Start with sources/ + detection/, then

enrichment/ + scoring/, then reports/ + CLI. After each module, show me

the file tree and a short test run before continuing.

