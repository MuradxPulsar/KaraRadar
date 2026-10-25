"""KaraRadar CLI entry point."""
import argparse
import os
import sys

if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _banner():
    try:
        import pyfiglet
        print(colors.header(pyfiglet.figlet_format("KaraRadar")))
    except Exception:
        print(colors.header("KaraRadar"))
    print(colors.header(r"""
                        .-=========-.
                     .-'             '-.
                   .'  .-===========-.  '.
                  /   /   .-------.   \   \
                 |   |   / (  ) (  )\   |   |
                 |   |  | (  ( (  )  ) |   |
                 |   |  | (  ( (  )  ) |   |
                 |   |   \ (  ) (  ) /   |   |
                  \   \   '-------'   /   /
                   '.  '-------------'  .'
                     '-.             .-'
                        '-=========-'
            RADAR MODE • Azərbaycan brand impersonation detector
"""))


from kararadar.core import colors, cache, report
from kararadar.core import spinner
from kararadar.detection import brandmatch, similarity
from kararadar.enrichment import rdap as rdapmod, dnsmod, ipinfo
from kararadar.sources import crtsh, certspotter
from kararadar.scoring import rules
from kararadar.reports import templates, html_gen
from kararadar.ai import ollama_sum
from kararadar.detection.brandmatch import load_brands
from kararadar.core.radar_anim import RadarAnimation
from kararadar import db, notify, i18n

BANNER = None


def is_whitelisted(d):
    return brandmatch.is_whitelisted(d)


def analyze_one(domain, lang="az", since=None):
    domain = domain.strip().lower()
    result = {
        "domain": domain,
        "whitelisted": False,
        "verdict": None,
        "score": 0,
        "signals": [],
        "brand_match": False,
        "matches": [],
        "rdap": None,
        "dns": None,
        "ip_list": [],
        "certs": [],
    }
    if brandmatch.is_whitelisted(domain):
        result["whitelisted"] = True
        result["verdict"] = "neytral"
        result["signals"] = [{"signal": "whitelist", "weight": 0,
                              "detail": templates.STRINGS[lang]["whitelist_note"]}]
        # cert email not needed
        return result

    # DNS
    dns = dnsmod.resolve(domain)
    result["dns"] = dns
    # RDAP (cached)
    C = cache.Cache()
    ri = C.get(f"rdap:{domain}")
    if ri is None:
        ri = rdapmod.lookup(domain)
        C.set(f"rdap:{domain}", ri)
    result["rdap"] = ri
    # IP enrichment
    ips = dns.get("A", [])
    ip_list = []
    for ip in ips:
        info = C.get(f"ip:{ip}")
        if info is None:
            info = ipinfo.lookup(ip)
            C.set(f"ip:{ip}", info)
        ip_list.append(info if isinstance(info, dict) else {"ip": ip})
    result["ip_list"] = ip_list

    # brand match
    brands = load_brands()
    matches = brandmatch.match(domain, brands)
    result["matches"] = matches
    result["brand_match"] = bool(matches)

    # since filter
    if since is not None and ri and isinstance(ri, dict):
        created = ri.get("created")
        if created:
            try:
                import datetime
                dt = datetime.datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                age = (datetime.datetime.now(datetime.timezone.utc) - dt).days
                if age > since:
                    # skip by returning None marker? We'll handle in caller; here store flag
                    result["_skip"] = True
            except Exception:
                pass

    scoring = rules.score_domain(domain, rdap=ri, dns=dns, ip_list=ip_list, brand_matches=matches)
    result["verdict"] = scoring["verdict"]
    result["score"] = scoring["score"]
    result["signals"] = scoring["signals"]
    result["brand_match"] = scoring["brand_match"]
    if result["brand_match"] is False and not matches:
        # add note
        pass
    # cert issuer info from crt.sh (optional)
    try:
        result["certs"] = crtsh.search_domain(domain, limit=5)
    except Exception:
        result["certs"] = []
    # cert email template
    result["cert_email"] = templates.cert_email(domain, result["verdict"], result["score"], result["signals"])
    try:
        C.record_run(domain, result["verdict"], result["score"])
    except Exception:
        pass
    finally:
        try:
            C.close()
        except Exception:
            pass
    return result


class _NullCtx:
    def __enter__(self): return self
    def __exit__(self, *a): return False


def analyze_domains(domains, lang="az", since=None, show=True, animated=True):
    out = []
    domains = [d for d in domains]
    use_anim = animated and sys.stdout.isatty() and not (len(domains) == 0)
    try:
        from kararadar.core.radar_anim import RadarAnimation
    except Exception:
        use_anim = False
    anim = RadarAnimation(enabled=use_anim) if use_anim else None
    ctx = anim if anim is not None else _NullCtx()
    with ctx:
        if anim is not None and anim.enabled:
            anim.set_total(len([d for d in domains if str(d).strip()]))
        for d in domains:
            d = d.strip() if isinstance(d, str) else d
            if not d:
                continue
            if anim is not None and anim.enabled:
                anim.set_current(d)
                anim.set_stage("DNS / RDAP / IP / Scoring")
            else:
                if show:
                    print(colors.scanning(f"Analyzing {d}..."))
            with spinner.Spinner(f"Analyzing {d}") if not (anim and anim.enabled) else _NullCtx():
                r = analyze_one(d, lang=lang, since=since)
            if r.get("_skip"):
                continue
            out.append(r)
            if anim is not None and anim.enabled:
                anim.advance()
                anim.add_blip(r.get("domain"), r.get("verdict"))
    # print results after animation
    if show:
        t = templates.STRINGS[lang]
        for r in out:
            import colorama
            col = colors.VERDICT_COLOR.get(r.get("verdict"), colorama.Fore.CYAN)
            body = []
            body.append(f"Domain: {r['domain']}")
            body.append(f"{t['verdict_label']}: {r.get('verdict')}   {t['score_label']}: {r.get('score')}")
            if r.get("whitelisted"):
                body.append(colors.ok(t["whitelist_note"]))
            elif not r.get("brand_match"):
                body.append(colors.info(t["no_brand"]))
            body.append("")
            body.append(t["signals_title"])
            for s in r.get("signals", []):
                body.append(f"  - {s.get('signal')} (+{s.get('weight')}): {s.get('detail')}")
            body.append("")
            body.append(f"{colors.info(t['advice'])}")
            body.append(f"{colors.warn(t['disclaimer'])}")
            colors.print_card("\n".join(body), col)
    return out


def monitor_brands(since=None, lang="az", limit=15, max_brands=8):
    brands = load_brands()[:max_brands]
    candidates = set()
    keywords = []
    for b in brands:
        for kw in (b.get("keywords") or [])[:2]:
            keywords.append(kw)
    keywords = list(dict.fromkeys(keywords))[:25]
    print(colors.header(f"[1/3] CT ma'lumot toplanmoqda ({len(keywords)} keyword)..."))
    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _search(kw):
        try:
            from kararadar.sources import crtsh
            return crtsh.search_keyword(kw, limit=80)
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=4) as ex:
        futs = {ex.submit(_search, kw): kw for kw in keywords}
        for fut in as_completed(futs):
            kw = futs[fut]
            try:
                ds = fut.result()
            except Exception:
                ds = []
            for d in ds:
                candidates.add(d)
            if len(candidates) >= 400:
                break
    print(colors.ok(f"[2/3] {len(candidates)} unikal domen tapildi"))
    cand_list = [d for d in candidates if not brandmatch.is_whitelisted(d)]
    cand_list = cand_list[:limit]
    print(colors.info(f"[3/3] {len(cand_list)} namizəd təhlil olunur"))
    print(colors.info(f"Discovered {len(candidates)} unique, analyzing {len(cand_list)}"))
    return analyze_domains(cand_list, lang=lang, since=since, show=True)

def add_brand(spec):
    # spec: Name|kw1,kw2|dom1,dom2
    parts = spec.split("|")
    name = parts[0].strip()
    kws = [x.strip() for x in parts[1].split(",")] if len(parts) > 1 else []
    doms = [x.strip() for x in parts[2].split(",")] if len(parts) > 2 else []
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "brands.yaml")
    # append using minimal text append
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"\n  - name: \"{name}\"\n")
        f.write(f"    keywords: [{', '.join('\"'+k+'\"' for k in kws)}]\n")
        f.write(f"    official_domains: [{', '.join('\"'+d+'\"' for d in doms)}]\n")
    print(colors.ok(f"Brand added: {name}"))


def remove_brand(name):
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "brands.yaml")
    brands = load_brands(path)
    brands = [b for b in brands if b.get("name") != name]
    # rewrite
    with open(path, "w", encoding="utf-8") as f:
        f.write("brands:\n")
        for b in brands:
            f.write(f"  - name: \"{b.get('name')}\"\n")
            ks = b.get("keywords", [])
            ds = b.get("official_domains", [])
            f.write(f"    keywords: [{', '.join('\"'+k+'\"' for k in ks)}]\n")
            f.write(f"    official_domains: [{', '.join('\"'+d+'\"' for d in ds)}]\n")
    print(colors.ok(f"Brand removed: {name}"))


def list_brands():
    for b in load_brands():
        print(b.get("name"), "-", b.get("official_domains"))


def interactive_menu(lang="az", show_banner=True):
    if show_banner:
        _banner()
    while True:
        print(colors.header("╔════════════════════════════════════════════════════════════════════════════╗"))
        print(colors.header("║ 🛰  KaraRadar — Interactive Menu                                           ║"))
        print(colors.header("╠════════════════════════════════════════════════════════════════════════════╣"))
        print(colors.header("║ 1 │ 🔍 Brand monitoring (CT discovery mode)                              ║"))
        print(colors.header("║ 2 │ 🌐 Analyze my own domains (domain1,domain2 or .txt)                  ║"))
        print(colors.header("║ 3 │ 🏷  Manage brands (add / remove / list — persists to brands.yaml)      ║"))
        print(colors.header("║ 4 │ ⚙️  Settings (language AZ/EN, report format)                           ║"))
        print(colors.header("║ 5 │ 👀 Watch mode (live CT stream with alerts)                            ║"))
        print(colors.header("║ 6 │ 📜 History & reports (browse past scans, diff)                        ║"))
        print(colors.header("║ 7 │ 🛡  Whitelist management (official domains)                           ║"))
        print(colors.header("║ 8 │ 🚪 Exit                                                              ║"))
        print(colors.header("╚════════════════════════════════════════════════════════════════════════════╝"))
        choice = input("> ").strip()
        if choice == "1":
            since_txt = input("Since N days (blank=all): ").strip().lower()
            if not since_txt or since_txt in ("n","all","*","none"):
                since = None
            else:
                try:
                    since = int(since_txt)
                except ValueError:
                    print(colors.warn("Sayı yanlışdır, hamısı istifadə olunur."))
                    since = None
            res = monitor_brands(since=since, lang=lang)
            _post_report(res, lang)
        elif choice == "2":
            inp = input("Domains separated by comma or .txt path: ").strip()
            if inp.endswith(".txt") and os.path.exists(inp):
                with open(inp, encoding="utf-8") as f:
                    domains = [x.strip() for x in f if x.strip()]
            else:
                domains = [x.strip() for x in inp.split(",")]
            res = analyze_domains(domains, lang=lang, show=True)
            _post_report(res, lang)
        elif choice == "3":
            sub = input("add/remove/list: ").strip().lower()
            if sub == "list":
                list_brands()
            elif sub == "add":
                spec = input("Name|kw1,kw2|domain1,domain2: ").strip()
                add_brand(spec)
            elif sub == "remove":
                name = input("Brand name: ").strip()
                remove_brand(name)
        elif choice == "4":
            l = input("Language az/en: ").strip().lower()
            if l in ("az", "en"):
                lang = l
            fmt = input("Default report format (txt/json/csv/html/md): ").strip()
            print(colors.ok(f"Language={lang}"))
        elif choice == "5":
            thr = input("Alert threshold score (default 40): ").strip()
            thr = int(thr) if thr else 40
            dur = input("Watch seconds (blank=30): ").strip()
            dur = int(dur) if dur else 30
            for _ in range(max(1, dur // 10)):
                res = monitor_brands(since=1, lang=lang, limit=20)
                for r in (res or []):
                    if (r.get("score") or 0) >= thr:
                        notify.alert(r.get("domain"), r.get("score"), r.get("verdict"), thr)
                import time as _t; _t.sleep(2)
        elif choice == "6":
            runs = db.history(10)
            for r in runs:
                print(f"Run {r['id']} {r['ts']:.0f} {r['lang']} -> {len(r['domains'])} domains")
            if len(runs) >= 2:
                diff = db.diff_runs(runs[1]["id"], runs[0]["id"])
                print("Diff new:", diff["new"])
                print("Diff gone:", diff["gone"])
                print("Diff changed:", diff["changed"])
        elif choice == "7":
            for b in load_brands():
                print(b.get("name"), "->", b.get("official_domains"))
        elif choice == "8":
            break
        else:
            print(colors.danger("Invalid choice"))


def _post_report(res, lang):
    if not res:
        return
    fmt = input("Export format (skip/json/csv/txt/html/md): ").strip().lower()
    if not fmt or fmt == "skip":
        return
    path = input("Output file path: ").strip()
    if not path:
        path = f"report.{fmt if fmt != 'markdown' else 'md'}"
    report.save(res, fmt, path, lang=lang)
    print(colors.ok(f"Saved {path}"))


def main():
    parser = argparse.ArgumentParser(prog="kararadar")
    parser.add_argument("--domains", type=str)
    parser.add_argument("--file", type=str)
    parser.add_argument("--add-brand", type=str)
    parser.add_argument("--remove-brand", type=str)
    parser.add_argument("--list-brands", action="store_true")
    parser.add_argument("--since", type=int)
    parser.add_argument("--ai", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--lang", choices=["az", "en"], default="az")
    parser.add_argument("-o", "--output", type=str)
    parser.add_argument("--enable-sandbox-view", action="store_true")
    parser.add_argument("--monitor", action="store_true")
    parser.add_argument("--no-banner", action="store_true")
    parser.add_argument("--brand", type=str)
    parser.add_argument("--watch", action="store_true")
    parser.add_argument("--format", type=str)
    parser.add_argument("--threshold", type=int, default=40)
    parser.add_argument("--demo-anim", action="store_true")
    args = parser.parse_args()

    lang = args.lang

    if args.add_brand:
        add_brand(args.add_brand); return
    if args.remove_brand:
        remove_brand(args.remove_brand); return
    if args.list_brands:
        list_brands(); return
    if args.brand:
        args.domains = args.brand

    if args.enable_sandbox_view:
        print(colors.warn("Sandbox view not implemented in Phase 1 (passive only)."))

    if args.demo_anim:
        from kararadar.core.radar_anim import RadarAnimation
        with RadarAnimation(enabled=True) as anim:
            anim.set_total(5)
            import time as _t
            for i in range(5):
                anim.set_current(f"demo-{i}.invalid")
                _t.sleep(1)
                anim.advance()
                anim.add_blip(f"demo-{i}.invalid", "infrastruktur şübhəsi" if i%2 else "brend təhliki şübhəsi")
        return
    # collect domains
    domains = []
    if args.domains:
        domains += [x.strip() for x in args.domains.split(",")]
    if args.file:
        with open(args.file, encoding="utf-8") as f:
            domains += [x.strip() for x in f if x.strip()]
    res = None
    if args.monitor or (not domains and not sys.stdin.isatty()):
        pass
    if domains:
        animated = not (args.no_anim or args.json)
        res = analyze_domains(domains, lang=lang, since=args.since, show=True, animated=animated)
    elif args.monitor:
        res = monitor_brands(since=args.since, lang=lang)
    else:
        try:
            interactive_menu(lang=lang, show_banner=(not args.no_banner))
        except (EOFError, KeyboardInterrupt):
            pass
        return

    if res is None:
        return
    # AI summary optional
    if args.ai:
        summary = ollama_sum.summarize(res)
        print(colors.header("AI Summary:"))
        print(summary)
    # output
    fmt = "json" if args.json else "txt"
    if args.output:
        ext = os.path.splitext(args.output)[1].lower().lstrip(".")
        if ext in ("html", "csv", "md", "json", "txt"):
            fmt = ext
        report.save(res, fmt, args.output, lang=lang)
        print(colors.ok(f"Saved {args.output}"))
    else:
        if args.json:
            print(report.to_json(res))
        else:
            print(colors.info("Kartlar yuxarida gosterildi. Fayla saxlamaq ucun -o istifade et."))


if __name__ == "__main__":
    main()
