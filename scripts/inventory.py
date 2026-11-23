#!/usr/bin/env python3
"""Scan a project for the design values it actually uses, compare them with a saved design system,
and (optionally) draft a first tokens.json when no design system exists yet.

Usage:
  python inventory.py <folder> [<folder> ...] [--tokens tokens.json] [--out report.json] [--draft-tokens draft.json]

Reads .css .html .htm .jsx .tsx .js .ts .vue .svelte .scss files (skips node_modules, dist, build, .git).
rem values are converted to px (1rem = 16px) so 0.875rem and 14px count as the same size.
9999px is counted as the pill radius (999px). Nothing in the project is modified. Standard library only.
"""
import sys, os, re, json, argparse, collections, datetime

EXT = {'.css', '.scss', '.html', '.htm', '.jsx', '.tsx', '.js', '.ts', '.vue', '.svelte'}
SKIP = {'node_modules', 'dist', 'build', '.git', '.next', 'vendor', 'coverage', 'out'}
MAX_BYTES = 6_000_000

def files(roots):
    for root in roots:
        if os.path.isfile(root):
            yield root
            continue
        for d, dirs, fs in os.walk(root):
            dirs[:] = [x for x in dirs if x not in SKIP and not x.startswith('.')]
            for f in fs:
                p = os.path.join(d, f)
                if os.path.splitext(f)[1].lower() in EXT and os.path.getsize(p) <= MAX_BYTES:
                    yield p

def norm_hex(h):
    h = h.lower()
    if len(h) == 4:
        h = '#' + ''.join(c * 2 for c in h[1:])
    return h

def rgb_of(h):
    return tuple(int(h[i:i + 2], 16) for i in (1, 3, 5))

def near(a, b, t=6):
    return sum(abs(x - y) for x, y in zip(rgb_of(a), rgb_of(b))) <= t * 3

def px(v):
    """Normalise a length to px text: '0.875rem' -> '14px', '9999px' -> '999px'. '%' stays as is."""
    v = v.strip()
    m = re.fullmatch(r'([0-9.]+)rem', v)
    if m:
        n = float(m.group(1)) * 16
        return ('%g' % round(n, 2)) + 'px'
    if v == '9999px':
        return '999px'
    return v

TW_RADIUS = {'rounded-none': '0px', 'rounded-sm': '2px', 'rounded': '4px', 'rounded-md': '6px', 'rounded-lg': '8px', 'rounded-xl': '12px', 'rounded-2xl': '16px', 'rounded-3xl': '24px', 'rounded-full': '999px'}
TW_TEXT = {'xs': '12px', 'sm': '14px', 'base': '16px', 'lg': '18px', 'xl': '20px', '2xl': '24px', '3xl': '30px', '4xl': '36px', '5xl': '48px', '6xl': '60px', '7xl': '72px', '8xl': '96px', '9xl': '128px'}

THEME_VARS = {}

def theme_vars(css):
    """(variable, 'light' or 'dark', hex) for every colour custom property, using the block it sits in.
    A block counts as dark when its selector or an enclosing @media mentions dark (.dark, [data-theme=dark], prefers-color-scheme: dark)."""
    out, stack, buf = [], [], ''
    for ch in css:
        if ch == '{':
            stack.append(buf.strip()); buf = ''
        elif ch == '}':
            if stack:
                sel = stack.pop()
                dark = any(re.search(r'dark|prefers-color-scheme:\s*dark', s, re.I) for s in stack + [sel])
                for k, v in re.findall(r'(--[A-Za-z0-9_-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b', buf):
                    out.append((k, 'dark' if dark else 'light', v))
            buf = ''
        else:
            buf += ch
    return out

def scan(roots):
    C = {k: collections.Counter() for k in ['color', 'radius', 'font-size', 'font-family', 'spacing', 'shadow', 'z-index', 'transition', 'keyframes', 'custom-property', 'class']}
    n = 0
    exts = collections.Counter()
    for p in files(roots):
        try:
            s = open(p, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        n += 1
        exts[os.path.splitext(p)[1].lower()] += 1
        css = ''.join(re.findall(r'<style[^>]*>(.*?)</style>', s, flags=re.S)) if p.lower().endswith(('.html', '.htm', '.vue', '.svelte')) else s
        for _v, _th, _hx in theme_vars(css):
            THEME_VARS.setdefault(_v, {})[_th] = norm_hex(_hx)
        for h in re.findall(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b', css):
            C['color'][norm_hex(h)] += 1
        for v in re.findall(r'border-radius:\s*([0-9.]+(?:px|rem|%))', css):
            C['radius'][px(v)] += 1
        for v in re.findall(r'font-size:\s*([0-9.]+(?:px|rem))', css):
            C['font-size'][px(v)] += 1
        for v in re.findall(r"font-family:\s*([^;}{]{3,80})", css):
            C['font-family'][v.strip().split(',')[0].strip(' \'"')] += 1
        for size, fam in re.findall(r"(?<![a-z-])font:\s*(?:[a-z0-9 ]*?\s)?([0-9.]+(?:px|rem))(?:/[0-9.]+(?:px|rem)?)?\s+([^;}{]{2,60})", css):
            C['font-size'][px(size)] += 1
            C['font-family'][fam.strip().split(',')[0].strip(' \'"')] += 1
        for v in re.findall(r'(?:gap|margin(?:-[a-z]+)?|padding(?:-[a-z]+)?):\s*([0-9.]+(?:px|rem))', css):
            C['spacing'][px(v)] += 1
        for v in re.findall(r'box-shadow:\s*([^;}{]{4,90})', css):
            v = v.strip()
            if v != 'none': C['shadow'][v] += 1
        for v in re.findall(r'z-index:\s*(-?\d+)', css):
            C['z-index'][v] += 1
        for v in re.findall(r'transition:\s*([^;}{]{3,60})', css):
            C['transition'][v.strip()] += 1
        for v in re.findall(r'@keyframes\s+([A-Za-z0-9_-]+)', css):
            C['keyframes'][v] += 1
        for k, v in re.findall(r'(--[A-Za-z0-9_-]+):\s*([^;}{]{1,60})', css):
            C['custom-property'][f'{k}: {v.strip()}'] += 1
        for k in re.findall(r'\.([A-Za-z][A-Za-z0-9_-]+)\s*[{,:.\[ >+~]', css):
            C['class'][k] += 1
        if p.lower().endswith(('.tsx', '.jsx', '.html', '.htm', '.vue', '.svelte', '.js', '.ts')):
            # Tailwind utility classes (default scale: 1 unit = 4px). Only inside class / className attributes.
            for attr in re.findall(r'(?:class|className)\s*=\s*(?:\{[^}]{0,400}\}|"[^"]{0,400}"|\'[^\']{0,400}\')', s):
                for _, name in re.findall(r'(?<![\w:-])((?:[a-z-]+:)*)(rounded(?:-(?:none|sm|md|lg|xl|2xl|3xl|full))?|text-(?:xs|sm|base|lg|[1-9]xl)|(?:p|m|gap)(?:[xytrbl])?-\d+(?:\.5)?)(?![\w-])', attr):
                    if name.startswith('rounded'):
                        r = TW_RADIUS.get(name)
                        if r: C['radius'][r] += 1
                    elif name.startswith('text-'):
                        C['font-size'][TW_TEXT[name[5:]]] += 1
                    else:
                        num = float(name.rsplit('-', 1)[1])
                        C['spacing'][('%g' % (num * 4)) + 'px'] += 1
    return C, n, exts

def token_values(path):
    t = json.load(open(path))
    vals = {'color': set(), 'radius': set(), 'font-size': set(), 'spacing': set()}
    def hexes(v):
        if isinstance(v, str): return [norm_hex(x) for x in re.findall(r'#[0-9a-fA-F]{3,6}\b', v)]
        if isinstance(v, dict): return [h for x in v.values() for h in hexes(x)]
        return []
    for tok in (t.get('color') or {}).get('tokens', []):
        vals['color'].update(hexes(tok.get('value')))
    for tok in (t.get('radius') or {}).get('tokens', []):
        vals['radius'].add(px(str(tok.get('value'))))
    for tok in (t.get('spacing') or {}).get('tokens', []):
        vals['spacing'].add(px(str(tok.get('value'))))
    for g in (t.get('type') or {}).get('groups', []):
        for st in g.get('styles', []):
            vals['font-size'].add(px(str(st.get('fontSize'))))
    return vals

def code_vars(C, path=None):
    """CSS custom properties that hold a colour, with the saved token (if any) whose value matches."""
    by_val = collections.defaultdict(list)
    if path:
        t = json.load(open(path))
        def add(name, v):
            if isinstance(v, str):
                for h in re.findall(r'#[0-9a-fA-F]{3,6}\b', v): by_val[norm_hex(h)].append(name)
            elif isinstance(v, dict):
                for x in v.values(): add(name, x)
        for tok in (t.get('color') or {}).get('tokens', []): add(tok['name'], tok.get('value'))
    out = []
    for item in C['custom-property']:
        k, _, v = item.partition(':')
        m = re.match(r'\s*(#[0-9a-fA-F]{3,6})\b', v)
        if m:
            out.append((k.strip(), norm_hex(m.group(1)), by_val.get(norm_hex(m.group(1))) or []))
    return out

def draft_tokens(C, roots, variables):
    """Build a first tokens.json from the scan. Values are what the code uses, not what anyone decided."""
    total = len(C['color'])
    thr = 1 if total <= 40 else 5
    cap = 20 if total <= 40 else 24
    var_name = {}
    for k, v, _ in variables:
        var_name.setdefault(v, k.lstrip('-'))
    used_names = set()
    def uniq(n):
        base, i = n, 2
        while n in used_names:
            n = f'{base}-{i}'; i += 1
        used_names.add(n); return n
    colors, used_hex = [], set()
    for var, th in sorted(THEME_VARS.items()):
        if th.get('light') and th.get('dark') and th['light'] != th['dark']:
            colors.append({'name': uniq(var.lstrip('-')), 'value': {'light': th['light'].upper(), 'dark': th['dark'].upper()}, 'usage': f'Code: `{var}`. Light and dark values read from the code. Not yet confirmed by a person.'})
            used_hex.update([th['light'], th['dark']])
    paired = len(colors)
    for h, c in C['color'].most_common():
        if c < thr or len(colors) >= cap + paired: break
        if h in used_hex: continue
        name = uniq(var_name.get(h) or 'color-' + h[1:])
        colors.append({'name': name, 'value': h.upper(), 'usage': f'Used {c} times in the scan. Source: code. Not yet confirmed by a person.'})
    fams = [f for f, _ in C['font-family'].most_common() if not f.startswith(('var(', 'inherit', '-apple', 'system-ui', 'sans-serif', 'serif', 'monospace', 'ui-'))][:3]
    sizes = [(s, c) for s, c in C['font-size'].most_common(40) if s.endswith('px')]
    sizes = sorted(sizes[:8], key=lambda x: float(x[0][:-2]))
    styles = [{'name': 'size-' + s[:-2], 'fontSize': s, 'lineHeight': 1.4, 'fontWeight': 400, 'usage': f'Used {c} times in the scan.'} for s, c in sizes]
    sp = sorted([(s, c) for s, c in C['spacing'].most_common(40) if s.endswith('px') and c >= 3][:10], key=lambda x: float(x[0][:-2]))
    rd = sorted([(s, c) for s, c in C['radius'].most_common(40) if c >= 2][:8], key=lambda x: (x[0].endswith('%'), float(re.sub(r'[^0-9.]', '', x[0]) or 0)))
    sh = [(s, c) for s, c in C['shadow'].most_common(4)]
    zi = sorted([(s, c) for s, c in C['z-index'].most_common(8)], key=lambda x: int(x[0]))
    return {
        'name': os.path.basename(os.path.abspath(roots[0])) + ' (draft)',
        'version': 0,
        'color': {'themes': [{'id': 'light', 'name': 'Light'}] + ([{'id': 'dark', 'name': 'Dark'}] if paired else []), 'tokens': colors},
        'type': {'fonts': [], 'families': {('serif' if i == 1 else 'sans' if i == 0 else 'accent'): f for i, f in enumerate(fams)}, 'groups': [{'name': 'Text', 'family': 'sans', 'styles': styles}]},
        'spacing': {'note': 'Drafted from a scan: the values the code uses most.', 'tokens': [{'name': 'space-' + s[:-2], 'value': s, 'usage': f'Used {c} times in the scan.'} for s, c in sp]},
        'radius': {'note': 'Drafted from a scan.', 'tokens': [{'name': 'radius-' + s.replace('%', 'pct').replace('px', ''), 'value': s, 'usage': f'Used {c} times in the scan.'} for s, c in rd]},
        'shadow': {'note': 'Drafted from a scan.', 'tokens': [{'name': f'shadow-{i + 1}', 'value': s, 'usage': f'Used {c} times in the scan.'} for i, (s, c) in enumerate(sh)]},
        'zindex': {'note': 'Drafted from a scan.', 'tokens': [{'name': 'z-' + s, 'value': s, 'usage': f'Used {c} times in the scan.'} for s, c in zi]},
        'draft': {'source': [os.path.abspath(r) for r in roots], 'date': datetime.date.today().isoformat(), 'status': 'DRAFT. What the code uses, not what anyone decided. A person must review every value.'},
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('roots', nargs='+')
    ap.add_argument('--tokens')
    ap.add_argument('--out')
    ap.add_argument('--draft-tokens')
    a = ap.parse_args()
    C, n, exts = scan(a.roots)
    variables = code_vars(C, a.tokens)
    rep = {'files_scanned': n, 'file_types': dict(exts), 'counts': {k: v.most_common(60) for k, v in C.items()}, 'code_variables': variables}
    lines = [f'# Design inventory ({n} files scanned)', '']
    def top(k, m=14):
        return ', '.join(f'{v} x{c}' for v, c in C[k].most_common(m)) or 'none'
    for k, title in [('color', 'Colours'), ('radius', 'Corner radii'), ('font-size', 'Font sizes'), ('font-family', 'Font families'), ('spacing', 'Spacing values'), ('shadow', 'Shadows'), ('z-index', 'Layers (z-index)'), ('keyframes', 'Animations')]:
        lines.append(f'**{title}** ({len(C[k])} distinct): {top(k)}')
    lines.append(f'**Style classes defined**: {len(C["class"])}')
    lines.append(f'**Colour variables in code**: {len(variables)}')
    cols = [c for c, _ in C['color'].most_common()]
    dups = []
    for i, x in enumerate(cols[:150]):
        for y in cols[i + 1:150]:
            if near(x, y): dups.append((x, y, C['color'][x], C['color'][y]))
    rep['near_duplicate_colors'] = dups[:40]
    if dups:
        lines += ['', '**Near-duplicate colours** (one may be a typo or an unrecorded variant):'] + [f'- {x} (x{cx}) and {y} (x{cy})' for x, y, cx, cy in dups[:15]]
    if a.tokens:
        tv = token_values(a.tokens)
        gaps = {}
        for k in ['color', 'radius', 'font-size', 'spacing']:
            miss = [(v, c) for v, c in C[k].most_common() if (norm_hex(v) if k == 'color' else v) not in tv[k]]
            gaps[k] = miss[:40]
        rep['not_in_tokens'] = gaps
        lines += ['', f'## Used in the project but NOT in {os.path.basename(a.tokens)}']
        for k in gaps:
            lines.append(f'- **{k}** ({len(gaps[k])}): ' + (', '.join(f'{v} x{c}' for v, c in gaps[k][:16]) or 'none'))
        lines += ['', '## Code variables and the token each one matches (by value)']
        lines += [f'- {k} = {v} -> ' + (', '.join(nm) if nm else 'NO MATCHING TOKEN') for k, v, nm in variables[:40]]
        unused = {k: sorted(tv[k] - {norm_hex(v) if k == 'color' else v for v in C[k]}) for k in tv}
        rep['in_tokens_not_used'] = unused
        lines += ['', '## In the tokens but never found in the code (maybe dropped, maybe only defined elsewhere)']
        for k, v in unused.items():
            lines.append(f'- **{k}**: ' + (', '.join(v) or 'none'))
    elif not a.draft_tokens:
        lines += ['', 'No tokens file given. Re-run with --draft-tokens draft.json to build a first design system from this scan.']
    print('\n'.join(lines))
    if a.out:
        json.dump(rep, open(a.out, 'w'), indent=1)
    if a.draft_tokens:
        d = draft_tokens(C, a.roots, variables)
        json.dump(d, open(a.draft_tokens, 'w'), indent=1)
        print(f"\nDraft design system written to {a.draft_tokens}: {len(d['color']['tokens'])} colours, {len(d['type']['groups'][0]['styles'])} text sizes, {len(d['spacing']['tokens'])} spacing, {len(d['radius']['tokens'])} radii.")

if __name__ == '__main__':
    main()
