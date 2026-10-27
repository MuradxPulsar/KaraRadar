# KaraRadar

![Python](https://img.shields.io/badge/python-3.12%2B-blue?logo=python)
![License](https://img.shields.io/badge/license-MIT-green)
![Tests](https://img.shields.io/badge/tests-13%20passed-brightgreen)
![Status](https://img.shields.io/badge/status-active-success)

**KaraRadar** is a passive OSINT anti-phishing CLI tool for detecting domains
that impersonate Azerbaijani brands. It performs **zero connections to target
websites** (Phase 1), requires **no API keys by default**, and runs on Windows 11
CMD with pure-Python dependencies. Reports are generated in **AZ & EN**.

> ⚠️ Automated early warning only. Not a full security solution. Human review is
> always required.

---

## ✨ What it does

- Discovers candidate domains via **certificate transparency** (crt.sh + CertSpotter)
- Detects brand impersonation:
  - Typosquatting (Levenshtein)
  - Homoglyphs (`l/1`, `o/0`, `rn/m`, Cyrillic↔Latin)
  - IDN / punycode
  - Added words (`login`, `secure`, `support`…)
  - TLD swaps
  - Hyphen insertion/removal
  - Adjacent-char transpositions
- Passive enrichment: **RDAP**, DNS (`A/MX/NS/TXT`), IP geolocation/ASN/proxy-hosting
  (ip-api.com)
- Email-security signals: SPF / DMARC presence
- **Transparent rule-based scoring** (no ML) with explicit weights
- Three verdicts only (never "malicious"):
  - `brend təhliki şübhəsi`
  - `infrastruktur şübhəsi`
  - `neytral`
- Reports: **JSON, CSV, TXT, HTML (dark/light + SVG graph), Markdown**
- CERT notification email template (`info@cert.gov.az`) — text only, never auto-sent
- Interactive menu + CLI flags
- 112 Azerbaijani brand presets with official-domain whitelist
- SQLite TTL cache + run history

## 🚫 What it does NOT do

- No SMS / social-media phishing detection
- No detection on legitimate-but-compromised sites
- No non-brand-lookalike domains
- No exploitation, brute-forcing, credential harvesting
- Phase 1 never connects to target websites

---

## 🎨 Tool appearance (CLI)

```
 _  __               ____           _            
| |/ /__ _ _ __ __ _|  _ \ __ _  __| | __ _ _ __ 
| ' // _` | '__/ _` | |_) / _` |/ _` |/ _` | '__|
| . \ (_| | | | (_| |  _ < (_| | (_| | (_| | |   
|_|\_\__,_|_|  \__,_|_| \_\__,_|\__,_|\__,_|_|   
                                                 
              _.-"""""""""-._
           .-'      |      '-.
         .'    .    |    *    '.
        /           |           \
       /     *      |      .     \
      |             |             |
      |----- - - - -+- - - - - ---|
      |             |\            |
       \       .    | \     *    /
        \           |  \         /
         '.         |   \      .'
           '-._     |    \  _.-'
               '""""""""""'
             [ scanning... ]
╔════════════════════════════════════════════════════════════════════════════╗
║ KaraRadar — Interactive Menu                                               ║
╠════════════════════════════════════════════════════════════════════════════╣
║ 1 │ Brand monitoring (CT discovery mode)                                    ║
║ 2 │ Analyze my own domains (domain1,domain2 or .txt)                       ║
║ 3 │ Manage brands (add / remove / list — persists to brands.yaml)           ║
║ 4 │ Settings (language AZ/EN, report format)                                ║
║ 5 │ Watch mode (live CT stream with alerts)                                ║
║ 6 │ History & reports (browse past scans, diff)                            ║
║ 7 │ Whitelist management (official domains)                               ║
║ 8 │ Exit                                                                  ║
╚════════════════════════════════════════════════════════════════════════════╝
+----------------------------------------------------------------------------+
| Domain: kapital-bank.az                                                    |
| Qərar: brend təhliki şübhəsi   Xal: 75                                    |
|                                                                            |
| NİYƏ?                                                                      |
|   - brand lookalike (typosquat) (+30): Levenshtein distance: 1              |
|   - suspicious words (+10): az                                             |
|                                                                            |
| [i] rəsmi kanalla yoxla                                                   |
| [w] Bu avtomatik ilkin qiymətləndirmədir, insan yoxlaması tələb olunur     |
+----------------------------------------------------------------------------+
```

## 📦 Installation

Use **Python 3.12 or 3.13** (not 3.15 — pyyaml wheels may be missing and
require MSVC build tools).

### Windows

```bat
git clone https://github.com/MuradxPulsar/KaraRadar.git
cd KaraRadar
py -3.12 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Do **not** use the `python` shim from `WindowsApps`; it may be unavailable.
If `python` is not found, call the interpreter by full path, e.g.
`C:\Users\<you>\AppData\Local\Programs\Python\Python312\python.exe`.

### Linux / macOS

```bash
git clone https://github.com/MuradxPulsar/KaraRadar.git
cd KaraRadar
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional (for YAML config weights):

```bash
pip install pyyaml
```

If this fails on your Python (e.g. 3.15 without MSVC), skip it — KaraRadar
falls back to its built-in minimal YAML parser and default weights.

---

## 🚀 Usage

### Interactive menu

```bash
python main.py
```

Shows ASCII banner + menu:
1. Brand monitoring (CT discovery)
2. Analyze your own domains
3. Manage brands (add/remove/list)
4. Settings (language, format)
5. Exit

### CLI

```bash
# analyze domains
python main.py --domains kapital-bank.az,azercell-login.xyz --lang az

# from file
python main.py --file domains.txt -o report.html

# CT brand monitoring
python main.py --monitor --since 7 --lang az -o stats.json

# export
python main.py --domains example.invalid --json
python main.py --domains example.invalid --lang en -o report.md

# brand management
python main.py --list-brands
python main.py --add-brand "Brand|kw1,kw2|dom1.com,dom2.com"
python main.py --remove-brand "Brand"

# optional local AI summary
python main.py --domains x.az --ai
```

### Key flags

| Flag | Meaning |
|---|---|
| `--domains` | comma-separated domains |
| `--file` | `.txt` list of domains |
| `--monitor` | CT discovery mode (brand monitoring) |
| `--since N` | only domains first seen in last N days |
| `--add-brand/--remove-brand/--list-brands` | manage `config/brands.yaml` |
| `--lang az\|en` | report language |
| `--json` | JSON output |
| `-o FILE` | output file (auto format by extension) |
| `--ai` | optional local Ollama summary (OFF by default) |
| `--enable-sandbox-view
--no-banner
--brand
--watch
--format
--threshold` | Phase 2 stub (read-only, default OFF) |

---

## 🛡 Whitelist (never flagged)

- Any `*.gov.az`, `*.edu.az`
- Any domain listed in a brand’s `official_domains`
- Noted in output: *"Rəsmi domain — avtomatik istisna"*

---

## 📊 Scoring (rule-based, transparent)

| Signal | Weight |
|---|---|
| Domain age < 30 days | +35 (strong) |
| Domain age < 90 days | +20 (medium) |
| Homoglyph / IDN (punycode) | +40 |
| Typosquat / Transposition | +30 / +25 |
| TLD swap | +25 |
| Added word / Hyphen merge | +20 / +15 |
| Suspicious words (login, secure, verify, bonus, az, support, update) | +10 each (cap 20) |
| Abused TLD (.top/.xyz/.buzz/.click/.live/.rest/.cam) | +25 |
| Missing SPF / DMARC | +8 each |
| Proxy / hosting flag | +15 each |
| Foreign hosting | +10 |
| **Aggregation bonus** (new + brand lookalike + registrar) | +20 |

Verdict thresholds: brand match → *brend təhliki şübhəsi*; otherwise score ≥ 40 →
*infrastruktur şübhəsi*; else *neytral*.

Every report ends with:  
*"Bu avtomatik ilkin qiymətləndirmədir, insan yoxlaması tələb olunur."*

---

## 🌐 Reports

- Export via `-o report.html|csv|md|json|txt`
- HTML includes a **dark/light toggle**, responsive cards and an **SVG relation graph**
  (shared IP / registrar / certificate links)
- CERT notification template printed (never sent automatically)

---

## 🧪 Tests

```bash
pytest
# expected: 13 passed
```

Offline tests cover: similarity on `example.invalid`, whitelist safety, scoring on
brand-match vs no-brand paths.

---

## ⚙️ Configuration

- Brands: `config/brands.yaml` (112 presets). Add/remove via CLI or edit file.
- SQLite cache: `~/.kararadar_cache.db` (TTL; purge supported)
- Optional: `config/scoring.yaml` for future weight overrides (roadmap)

---

## 📌 Known limitations / honesty

- CT sources are rate-limited; failures are logged and skipped
- RDAP coverage varies by registrar
- ip-api free tier is rate-limited
- The minimal YAML parser is used when `pyyaml` is unavailable (Python 3.15)
- Brands list is a starter/preset set; community can extend
- False positives expected — human review required

---

## 🧩 Project structure

```
kararadar/
├── kararadar/
│   ├── main.py  core/  sources/  detection/  enrichment/
│   ├── scoring/  reports/  ai/
├── config/brands.yaml
├── tests/test_detection.py
├── setup.py  requirements.txt  README.md  LICENSE
└── .github/workflows/daily.yml
```

---

## 🔒 Safety (non-negotiable)

- Phase 1: zero connections to target websites
- No exploitation, brute-force, or credential harvesting
- Public disclosure only of **aggregate statistics**, never individual domains

---

## 🏛 CERT reporting

Report suspicious domains to **info@cert.gov.az**. KaraRadar generates the
email text only; nothing is sent automatically.

---

## 📚 Sources

- [crt.sh](https://crt.sh/) certificate transparency
- [CertSpotter API v1](https://api.certspotter.com/)
- [RDAP (rdap.org)](https://rdap.org)
- [ip-api.com](https://ip-api.com) (free)
- [dnspython](https://www.dnspython.org/)

---

## ⚖️ License

MIT.

---

## Added (polish phase)

- Watch mode, history & diff, whitelist management menu options
- AZ normalization + subdomain trick detection
- Config/rules YAML + hot-reload scoring weights
- HTTP safe probe (no form submission)
- Reputation lookups (optional API keys)
- CI workflow (pytest on push/PR)
- Brand variant generator

## Animation

- Live radar animation runs during scans (green theme, ~12 FPS).
- Non-TTY/CI mode prints a one-line frame every ~2 seconds.
- Disable with `--json` or `--no-anim`.
- Preview: `python main.py --demo-anim`.

## 🤖 Disclosure

**AI-assisted development.**

"Early warning, not complete protection."

## Function Reference

### kararadar.ai
- ollama_sum.summarize(results)

### kararadar.core
- cache:
  - class `Cache(path=DEFAULT_DB, ttl=86400)`
  - methods: `get(key)`, `set(key, value, ttl=None)`, `record_run(domain, verdict, score)`, `trend(limit=30)`, `purge()`, `close()`, context manager `__enter__`/`__exit__`.
- colors:
  - `_strip_ansi(s)`
  - `ok(msg)`, `success(msg)`, `danger(msg)`, `error(msg)`, `info(msg)`, `header(msg)`, `warn(msg)`, `scanning(msg)`, `gradient(msg)`
  - `card(text, color=Fore.CYAN)`, `print_card(body, color=None)`
  - constant `VERDICT_COLOR`.
- radar_anim:
  - classes: `RadarState`, `RadarAnimation(message="Scanning...", enabled=True)`
  - functions: `_tty()`, `_cols()`, `_hide_cursor()`, `_show_cursor()`, `_pos(domain, radius=9)`, `render_frame(state, width=32)`, `with_radar(text="Scanning...")`, `log_checked(msg)`, `_color_ok()`
  - `RadarAnimation` methods: `__enter__`, `__exit__`, `stop()`, `set_stage(stage)`, `set_current(domain)`, `advance(error=False)`, `add_blip(domain, verdict)`, `set_total(n)`, plus internal runners `_run`, `_run_lines`, `_stop_frame`.
- report:
  - `to_json(results)`, `to_txt(results, lang="az")`, `to_csv(results)`, `to_md(results, lang="az")`, `to_html(results, lang="az")`, `save(results, fmt, path, lang="az")`.
- spinner:
  - class `Spinner(message)` (context manager).
  - cache `record_run`/`trend` helpers as above.

### kararadar.db
- `_conn(path=None)`
- `record_run(run_id=None, domains=None, lang="az")`
- `mark_seen(domain)`
- `history(limit=10)`
- `diff_runs(a_id, b_id)`

### kararadar.detection
- brandmatch:
  - `_simple_parse(path)`
  - `load_brands(path=None)`
  - `is_whitelisted(domain)`
  - `match(candidate, brands=None)`
- similarity:
  - `levenshtein(a, b)`
  - `normalize_domain(d)`
  - `registered_name(domain)`
  - `is_punycode(domain)`
  - `homoglyph_normalize(s)`
  - `az_normalize(s)`
  - `detect(candidate, brand)`
  - `has_suspicious_word(domain)`
  - `abused_tld(domain)`
  - `generate_variants(name)`
  - constants: `HOMOGLYPHS`, `SUSPICIOUS_WORDS`, `ABUSED_TLDS`, `AZ_MAP`.

### kararadar.enrichment
- dnsmod.resolve(domain)
- ipinfo.lookup(ip)
- probe.probe(url, timeout=10), `_title(html)`
- rdap.lookup(domain)

### kararadar.i18n
- `t(lang, key)`

### kararadar.main
- `_banner()`
- class `_NullCtx`
- `is_whitelisted(d)`
- `analyze_one(domain, lang="az", since=None)`
- `analyze_domains(domains, lang="az", since=None, show=True, animated=True)`
- `monitor_brands(since=None, lang="az", limit=15, max_brands=8)`
- `add_brand(spec)`
- `remove_brand(name)`
- `list_brands()`
- `interactive_menu(lang="az", show_banner=True)`
- `_post_report(res, lang)`
- `main()`

### kararadar.notify
- `alert(domain, score, verdict, threshold=40)`

### kararadar.reports
- templates:
  - `STRINGS`, `CERT_EMAIL_TEMPLATE`, `cert_email(domain, verdict, score, signals)`
- html_gen:
  - `_svg_graph(results)`
  - `generate(results, lang="az")`

### kararadar.scoring
- rules:
  - `_load_weights()`
  - `W(key, default=None)`
  - `_age_days(created)`
  - `score_domain(domain, rdap=None, dns=None, ip_list=None, brand_matches=None)`
  - constants: `SUSPICIOUS_WORDS`, `ABUSED_TLDS`, `BRAND_WEIGHTS`, `WEIGHTS`, `_DEFAULTS`, `_LOADED`.

### kararadar.sources
- certspotter.get_issuances(domain, limit=50)
- crtsh:
  - `_get(params)`
  - `_collect_domains(data)`
  - `search_keyword(keyword, limit=200, include_expired=False)`
  - `search_keyword_status(keyword, limit=200, include_expired=False)`
  - `search_domain(domain, limit=100, include_expired=False, q_format="domain")`
  - `enumerate_subdomains(domain, limit=500)`
- reputation:
  - `virustotal(domain)`
  - `urlhaus(domain)`

### urls / notes
- Functions prefixed with `_` are internal helpers but listed above for completeness.

