"""Report exporters: TXT, JSON, CSV, HTML, Markdown."""
import csv
import json
import os
from ..reports import html_gen, templates

def _base(results):
    return results

def to_json(results):
    return json.dumps(results, indent=2, ensure_ascii=False, default=str)

def to_txt(results, lang="az"):
    t = templates.STRINGS.get(lang, templates.STRINGS["az"])
    lines = [t["title"], "=" * 40]
    for r in results:
        lines.append(f"\n{r.get('domain')}")
        lines.append(f"{t['verdict_label']}: {r.get('verdict')}  {t['score_label']}: {r.get('score')}")
        lines.append(t["signals_title"])
        for s in r.get("signals", []):
            lines.append(f"  - {s.get('signal')} (+{s.get('weight')}): {s.get('detail')}")
        lines.append(t["disclaimer"])
    return "\n".join(lines)

def to_csv(results):
    if not results:
        return ""
    fields = ["domain", "verdict", "score", "brand_match"]
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    w.writeheader()
    for r in results:
        w.writerow({k: r.get(k) for k in fields})
    return buf.getvalue()

def to_md(results, lang="az"):
    t = templates.STRINGS.get(lang, templates.STRINGS["az"])
    lines = [f"# {t['title']}", ""]
    for r in results:
        lines.append(f"## {r.get('domain')}")
        lines.append(f"- **{t['verdict_label']}:** {r.get('verdict')}")
        lines.append(f"- **{t['score_label']}:** {r.get('score')}")
        lines.append(f"- {t['signals_title']}")
        for s in r.get("signals", []):
            lines.append(f"  - {s.get('signal')} (+{s.get('weight')}): {s.get('detail')}")
        lines.append(f"*{t['disclaimer']}*")
        lines.append("")
    return "\n".join(lines)

def to_html(results, lang="az"):
    return html_gen.generate(results, lang)

def save(results, fmt, path, lang="az"):
    fmt = fmt.lower()
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    if fmt == "json":
        content = to_json(results)
    elif fmt == "csv":
        content = to_csv(results)
    elif fmt == "html":
        content = to_html(results, lang)
    elif fmt == "md" or fmt == "markdown":
        content = to_md(results, lang)
    else:
        content = to_txt(results, lang)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path