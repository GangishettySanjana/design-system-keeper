#!/usr/bin/env python3
"""Turn a tokens.json (and optional docs folder) into something people can use.

Usage:
  python export_system.py <tokens.json> --format html|pdf|css|tailwind|agents [--docs folder] [--out file] [--title "Name"]

  html      one self-contained, print-ready page: cover, colour (light and dark), type, spacing, radius, shadows, layers,
            then every markdown file in --docs. Open in a browser, or use it as the source for an artifact.
  pdf       the same page printed to PDF with Google Chrome (needs Chrome installed).
  css       CSS custom properties, with a dark-theme block when the tokens have dark values.
  tailwind  a tailwind.config theme.extend snippet that points at the CSS variables.
  agents    an AGENTS.md of always-on rules for AI agents: the tokens, what each is for, and how to use them.

Standard library only (Chrome is only needed for pdf).
"""
import sys, os, re, json, argparse, html, subprocess, shutil, datetime

e = html.escape

def val(v, theme='light'):
    if isinstance(v, dict):
        return v.get(theme) or v.get('light') or next(iter(v.values()))
    return v

def slug(n):
    return re.sub(r'[^a-z0-9]+', '-', str(n).lower()).strip('-')

def build_css(t):
    light, dark = [], []
    for c in (t.get('color') or {}).get('tokens', []):
        n = slug(c['name'])
        light.append(f'  --color-{n}: {val(c["value"])};')
        if isinstance(c['value'], dict) and c['value'].get('dark'):
            dark.append(f'  --color-{n}: {c["value"]["dark"]};')
    for s in (t.get('spacing') or {}).get('tokens', []):
        light.append(f'  --{slug(s["name"])}: {s["value"]};')
    for r in (t.get('radius') or {}).get('tokens', []):
        light.append(f'  --{slug(r["name"])}: {r["value"]};')
    for s in (t.get('shadow') or {}).get('tokens', []):
        light.append(f'  --{slug(s["name"])}: {s["value"]};')
    for z in (t.get('zindex') or {}).get('tokens', []):
        light.append(f'  --{slug(z["name"])}: {z["value"]};')
    for k, f in ((t.get('type') or {}).get('families') or {}).items():
        light.append(f'  --font-{slug(k)}: {f};')
    for g in (t.get('type') or {}).get('groups', []):
        for s in g.get('styles', []):
            light.append(f'  --text-{slug(s["name"])}: {s.get("fontSize")};')
    out = ['/* Generated from tokens.json. Do not edit by hand: change the tokens and export again. */', ':root {'] + light + ['}']
    if dark:
        out += ['', '@media (prefers-color-scheme: dark) {', '  :root:not([data-theme="light"]) {'] + ['  ' + d for d in dark] + ['  }', '}', '', ':root[data-theme="dark"] {'] + dark + ['}']
    return '\n'.join(out) + '\n'

def build_tailwind(t):
    def m(items, prefix='', key='name'):
        return ',\n      '.join(f"'{slug(i[key]).replace(prefix, '', 1) if prefix else slug(i[key])}': 'var(--{prefix}{slug(i[key]).replace(prefix, '', 1) if prefix else slug(i[key])})'" for i in items)
    colors = ',\n      '.join(f"'{slug(c['name'])}': 'var(--color-{slug(c['name'])})'" for c in (t.get('color') or {}).get('tokens', []))
    spacing = ',\n      '.join(f"'{slug(s['name']).replace('space-', '')}': 'var(--{slug(s['name'])})'" for s in (t.get('spacing') or {}).get('tokens', []))
    radius = ',\n      '.join(f"'{slug(r['name']).replace('radius-', '')}': 'var(--{slug(r['name'])})'" for r in (t.get('radius') or {}).get('tokens', []))
    shadow = ',\n      '.join(f"'{slug(s['name']).replace('shadow-', '')}': 'var(--{slug(s['name'])})'" for s in (t.get('shadow') or {}).get('tokens', []))
    fams = ',\n      '.join(f"'{slug(k)}': ['var(--font-{slug(k)})']" for k in ((t.get('type') or {}).get('families') or {}))
    return ('// Generated from tokens.json. Add this to tailwind.config.js and load the CSS from the "css" export.\n'
            'module.exports = {\n  theme: {\n    extend: {\n'
            f'    colors: {{\n      {colors}\n    }},\n    spacing: {{\n      {spacing}\n    }},\n    borderRadius: {{\n      {radius}\n    }},\n'
            f'    boxShadow: {{\n      {shadow}\n    }},\n    fontFamily: {{\n      {fams}\n    }},\n    }},\n  }},\n}};\n')

def build_agents(t, title):
    L = [f'# {title}: design rules for AI agents', '',
         'Always follow these rules when you build or change any screen. Use the tokens below by name. Never invent a colour, size, radius or spacing value that is not listed. If you need one, say so and ask a person.', '']
    ct = (t.get('color') or {}).get('tokens', [])
    if ct:
        L += ['## Colour tokens', '']
        for c in ct:
            v = c['value']
            vs = f'light {v.get("light")}, dark {v.get("dark")}' if isinstance(v, dict) else str(v)
            L.append(f'- `{c["name"]}` ({vs}): {c.get("usage", "")}')
        L.append('')
    for key, label in (('spacing', 'Spacing'), ('radius', 'Corner radius'), ('shadow', 'Shadows'), ('zindex', 'Layers')):
        toks = (t.get(key) or {}).get('tokens', [])
        if toks:
            L += [f'## {label}', '']
            if (t.get(key) or {}).get('note'): L += [t[key]['note'], '']
            L += [f'- `{x["name"]}` = {x["value"]}: {x.get("usage", "")}' for x in toks] + ['']
    groups = (t.get('type') or {}).get('groups', [])
    if groups:
        L += ['## Type', '']
        for k, f in ((t.get('type') or {}).get('families') or {}).items(): L.append(f'- {k}: {f}')
        for g in groups:
            for s in g.get('styles', []):
                L.append(f'- `{s["name"]}`: {s.get("fontSize")}, weight {s.get("fontWeight", 400)}. {s.get("usage", "")}')
        L.append('')
    L += ['## Before you finish', '', '- Every value you used is a token above.', '- Text contrast is at least 4.5:1 in every theme.', '- Tap targets are at least 44px.', '- If the product and these rules disagree, do not guess: tell the person.', '']
    return '\n'.join(L)

def md_to_html(md):
    out, in_ul, in_tbl = [], False, False
    def inline(s):
        s = e(s)
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        s = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', s)
        return s
    for raw in md.split('\n'):
        l = raw.rstrip()
        if in_ul and not l.lstrip().startswith(('- ', '* ')):
            out.append('</ul>'); in_ul = False
        if in_tbl and not l.startswith('|'):
            out.append('</table>'); in_tbl = False
        if not l.strip():
            continue
        m = re.match(r'(#{1,4})\s+(.*)', l)
        if m:
            lv = len(m.group(1)) + 1
            out.append(f'<h{lv}>{inline(m.group(2))}</h{lv}>')
        elif l.lstrip().startswith(('- ', '* ')):
            if not in_ul: out.append('<ul>'); in_ul = True
            out.append(f'<li>{inline(l.lstrip()[2:])}</li>')
        elif l.startswith('|'):
            if re.match(r'\|[\s:|-]+\|?$', l): continue
            cells = [c.strip() for c in l.strip('|').split('|')]
            if not in_tbl:
                out.append('<table>'); in_tbl = True
                out.append('<tr>' + ''.join(f'<th>{inline(c)}</th>' for c in cells) + '</tr>')
            else:
                out.append('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in cells) + '</tr>')
        elif l.startswith('---'):
            continue
        else:
            out.append(f'<p>{inline(l)}</p>')
    if in_ul: out.append('</ul>')
    if in_tbl: out.append('</table>')
    return '\n'.join(out)

def build_html(t, docs, title):
    ct = (t.get('color') or {}).get('tokens', [])
    sw = ''.join('<div class="sw"><div class="chip"><i style="background:%s"></i><i style="background:%s"></i></div><b>%s</b><span>%s</span><em>%s</em></div>' % (
        val(c['value'], 'light'), val(c['value'], 'dark'), e(c['name']), e(val(c['value'], 'light')) + ((' / ' + e(val(c['value'], 'dark'))) if isinstance(c['value'], dict) and c['value'].get('dark') else ''), e(c.get('usage', ''))) for c in ct)
    fams = (t.get('type') or {}).get('families') or {}
    ty = ''
    for g in (t.get('type') or {}).get('groups', []):
        ty += f'<h3>{e(g["name"])}</h3>'
        for s in g.get('styles', []):
            fam = fams.get(g.get('family'), 'inherit')
            try: px = min(int(float(re.sub(r"[^0-9.]", "", str(s.get('fontSize', '14'))) or 14)), 56)
            except ValueError: px = 14
            ty += f'<div class="ts"><div style="font-family:{e(fam)};font-size:{px}px;font-weight:{s.get("fontWeight", 400)}">Pick stops together</div><span>{e(s["name"])} &middot; {e(str(s.get("fontSize")))} &middot; {e(s.get("usage", ""))}</span></div>'
    def rows(key, fn):
        return ''.join(fn(x) for x in (t.get(key) or {}).get('tokens', []))
    sp = rows('spacing', lambda x: f'<div class="sp"><i style="width:{e(str(x["value"]))}"></i><span>{e(x["name"])} &middot; {e(str(x["value"]))} &middot; {e(x.get("usage", ""))}</span></div>')
    rd = rows('radius', lambda x: f'<div class="rd"><i style="border-radius:{e(str(x["value"]))}"></i><span>{e(x["name"])}<br>{e(str(x["value"]))}</span></div>')
    shd = rows('shadow', lambda x: f'<div class="sh"><i style="box-shadow:{e(str(x["value"]))}"></i><span>{e(x["name"])} &middot; {e(x.get("usage", ""))}</span></div>')
    zi = rows('zindex', lambda x: f'<li><code>{e(x["name"])}</code> = {e(str(x["value"]))}: {e(x.get("usage", ""))}</li>')
    docs_html = ''
    for name, md in docs:
        docs_html += f'<section class="doc"><div class="src">{e(name)}</div>{md_to_html(md)}</section>'
    draft = t.get('draft')
    note = f'<div class="draft">{e(draft["status"])} Source: {e(", ".join(draft["source"]))}. Scanned {e(draft["date"])}.</div>' if draft else ''
    css = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Instrument+Serif&display=swap');
@page{size:A4;margin:14mm}
*{box-sizing:border-box;margin:0}body{font-family:Inter,system-ui,sans-serif;font-size:10pt;line-height:1.5;color:#1E1E1B;background:#fff;padding:0 4mm}
h1,h2,h3,h4,h5{font-family:'Instrument Serif',Georgia,serif;font-weight:400}
.cover{min-height:250mm;display:flex;flex-direction:column;justify-content:flex-end;padding-bottom:20mm;page-break-after:always}
.cover h1{font-size:54pt;line-height:1}.cover p{max-width:130mm;color:#4A4940;margin-top:6mm;font-size:12pt}
.tag{font-size:9pt;letter-spacing:.1em;text-transform:uppercase;color:#6F6E62;margin-bottom:6mm}
h2{font-size:24pt;margin:8mm 0 4mm;border-bottom:.4mm solid #1E1E1B;padding-bottom:2mm;page-break-before:always}h2.first{page-break-before:auto}
h3{font-size:14pt;margin:5mm 0 2mm}h4{font-size:12pt;margin:4mm 0 1mm}h5{font-size:11pt;margin:3mm 0 1mm}
.swg{display:grid;grid-template-columns:repeat(3,1fr);gap:5mm}.sw .chip{display:flex;height:16mm;border-radius:3mm;overflow:hidden;border:.3mm solid #D7D4C8}.sw .chip i{flex:1}
.sw b{display:block;margin-top:1.5mm;font-size:9pt}.sw span{font-size:8pt;color:#6F6E62;display:block}.sw em{font-style:normal;font-size:7.5pt;color:#4A4940;display:block}
.ts{margin-bottom:3mm}.ts span{font-size:8pt;color:#6F6E62;display:block}
.sp{display:flex;align-items:center;gap:4mm;margin-bottom:2mm;font-size:8.5pt}.sp i{display:block;height:4mm;background:#C8371F;border-radius:1mm;flex:none}
.rdg{display:flex;flex-wrap:wrap;gap:5mm}.rd{width:24mm;font-size:8pt}.rd i{display:block;width:24mm;height:18mm;border:.5mm solid #1E1E1B;background:#fff;margin-bottom:1mm}
.sh{display:flex;align-items:center;gap:6mm;margin-bottom:5mm;font-size:8.5pt}.sh i{display:block;width:30mm;height:16mm;background:#fff;border-radius:3mm;flex:none}
.doc{margin-top:8mm}.doc .src{font-size:8pt;letter-spacing:.06em;text-transform:uppercase;color:#6F6E62;margin-bottom:2mm;page-break-before:always}
.doc p,.doc li{font-size:9.5pt}.doc ul{margin:1mm 0 2mm 5mm}.doc code,li code{font-family:ui-monospace,Menlo,monospace;font-size:8.5pt;background:#F3F1EA;padding:0 1mm;border-radius:1mm}
table{border-collapse:collapse;width:100%;margin:2mm 0;font-size:8.5pt}th{background:#F3F1EA;text-align:left}th,td{border:.25mm solid #D7D4C8;padding:1.4mm 2mm;vertical-align:top}tr{page-break-inside:avoid}
.draft{border-left:1mm solid #C8371F;background:#F7F5EF;padding:3mm 4mm;margin:4mm 0;font-size:9pt}
"""
    body = (f'<div class="cover"><div class="tag">Design system</div><h1>{e(title)}</h1><p>Tokens, type, spacing, shape and the rules that go with them, exported from the design system file on {datetime.date.today().isoformat()}.</p>{note}</div>'
            f'<h2 class="first">Colour</h2><div class="swg">{sw}</div>'
            f'<h2>Type</h2>{ty}<h2>Spacing</h2>{sp}<h2>Corner radius</h2><div class="rdg">{rd}</div>'
            + (f'<h2>Shadows</h2>{shd}' if shd else '') + (f'<h2>Layers</h2><ul>{zi}</ul>' if zi else '') + docs_html)
    return f'<!doctype html><html><head><meta charset="utf-8"><title>{e(title)}</title><style>{css}</style></head><body>{body}</body></html>'

def find_chrome():
    for p in ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'):
        if os.path.exists(p): return p
    return shutil.which('google-chrome') or shutil.which('chromium')

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tokens')
    ap.add_argument('--format', required=True, choices=['html', 'pdf', 'css', 'tailwind', 'agents'])
    ap.add_argument('--docs')
    ap.add_argument('--out')
    ap.add_argument('--title')
    a = ap.parse_args()
    t = json.load(open(a.tokens))
    title = a.title or t.get('name') or 'Design system'
    docs = []
    if a.docs and os.path.isdir(a.docs):
        order = ['README.md']
        files = []
        for d, _, fs in os.walk(a.docs):
            for f in sorted(fs):
                if f.lower().endswith('.md'):
                    files.append(os.path.relpath(os.path.join(d, f), a.docs))
        files.sort(key=lambda n: (0 if n == 'README.md' else 1 if '/' not in n else 2, n))
        for n in files:
            docs.append((n, open(os.path.join(a.docs, n), encoding='utf-8', errors='ignore').read()))
    f = a.format
    out = a.out or ('design-system.' + {'html': 'html', 'pdf': 'pdf', 'css': 'css', 'tailwind': 'tailwind.config.js', 'agents': 'AGENTS.md'}[f])
    if f == 'css': open(out, 'w').write(build_css(t))
    elif f == 'tailwind': open(out, 'w').write(build_tailwind(t))
    elif f == 'agents': open(out, 'w').write(build_agents(t, title))
    else:
        h = build_html(t, docs, title)
        if f == 'html':
            open(out, 'w').write(h)
        else:
            tmp = os.path.splitext(out)[0] + '.html'
            open(tmp, 'w').write(h)
            chrome = find_chrome()
            if not chrome:
                print(f'Chrome was not found. Open {tmp} in a browser and print it to PDF (Save as PDF).')
                return
            subprocess.run([chrome, '--headless=new', '--disable-gpu', '--no-pdf-header-footer', '--virtual-time-budget=15000', f'--print-to-pdf={os.path.abspath(out)}', 'file://' + os.path.abspath(tmp)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print(f'Wrote {out} ({os.path.getsize(out)} bytes)')

if __name__ == '__main__':
    main()
