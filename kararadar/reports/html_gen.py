"""HTML report generator with simple SVG relation graph."""
from .templates import STRINGS

def _svg_graph(results):
    domains = [r.get("domain") for r in results]
    n = len(domains)
    if n == 0:
        return ""
    # positions on circle
    import math
    cx, cy, radius = 300, 200, 140
    pos = {}
    for i, d in enumerate(domains):
        ang = 2 * math.pi * i / max(n, 1)
        pos[d] = (cx + radius * math.cos(ang), cy + radius * math.sin(ang))
    lines = []
    # edges by shared registrar
    for i in range(n):
        for j in range(i + 1, n):
            a = results[i]; b = results[j]
            same = False
            ra = (a.get("rdap") or {}).get("registrar")
            rb = (b.get("rdap") or {}).get("registrar")
            if ra and ra == rb:
                same = True
            # shared IP
            ips_a = set()
            for ip in (a.get("ip_list") or []):
                if isinstance(ip, dict):
                    ips_a.add(ip.get("ip"))
            ips_b = set()
            for ip in (b.get("ip_list") or []):
                if isinstance(ip, dict):
                    ips_b.add(ip.get("ip"))
            if ips_a and ips_b and ips_a & ips_b:
                same = True
            if same:
                lines.append(f'<line x1="{pos[domains[i]][0]:.0f}" y1="{pos[domains[i]][1]:.0f}" '
                            f'x2="{pos[domains[j]][0]:.0f}" y2="{pos[domains[j]][1]:.0f}" '
                            f'stroke="#999" stroke-width="1.5"/>')
    nodes = "".join(
        f'<circle cx="{pos[d][0]:.0f}" cy="{pos[d][1]:.0f}" r="14" fill="#4f46e5"/>'
        f'<text x="{pos[d][0]:.0f}" y="{pos[d][1]+4:.0f}" font-size="9" text-anchor="middle" fill="white">{d[:10]}</text>'
        for d in domains
    )
    return (f'<svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">'
            f'{"".join(lines)}{nodes}</svg>')


def generate(results, lang="az"):
    t = STRINGS.get(lang, STRINGS["az"])
    rows = ""
    for r in results:
        sigs = "".join(f"<li>{s.get('signal')} (+{s.get('weight')}): {s.get('detail')}</li>"
                       for s in r.get("signals", []))
        rows += f"""<div class="card">
<h3>{r.get('domain')}</h3>
<p><strong>{t['verdict_label']}:</strong> {r.get('verdict')} &nbsp; <strong>{t['score_label']}:</strong> {r.get('score')}</p>
<p>{t['signals_title']}</p><ul>{sigs or '<li>-</li>'}</ul>
<p class="note">{t['disclaimer']}</p>
</div>"""
    graph = _svg_graph(results)
    html = f"""<!DOCTYPE html>
<html lang="{lang}"><head><meta charset="utf-8"><title>{t['title']}</title>
<style>
:root{{--bg:#f5f5f7;--fg:#1f2937;--card:#fff;}}
[data-theme="dark"]{{--bg:#111827;--fg:#e5e7eb;--card:#1f2937;}}
body{{font-family:Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--fg);margin:0;padding:20px;transition:background .2s,color .2s;}}
h1{{color:var(--fg);}}.card{{background:var(--card);border-radius:10px;padding:16px;margin:12px 0;box-shadow:0 2px 6px rgba(0,0,0,.08);}}
.note{{font-size:.85em;color:#9ca3af;font-style:italic;}}
.toggle{{position:fixed;top:12px;right:12px;padding:6px 10px;cursor:pointer;border-radius:6px;border:1px solid #999;background:var(--card);color:var(--fg);}}
</style>
<script>function toggleTheme(){{const t=document.documentElement.getAttribute('data-theme')==='dark'?'light':'dark';document.documentElement.setAttribute('data-theme',t);localStorage.setItem('theme',t);}}(function(){{const t=localStorage.getItem('theme)||'light';document.documentElement.setAttribute('data-theme',t);}})();</script></head><body>
<button class="toggle" onclick="toggleTheme()">Toggle theme</button>
<h1>{t['title']}</h1>
{rows}
<h2>Relation graph</h2>
{graph}
<p class="note">{t['disclaimer']}</p>
</body></html>"""
    return html