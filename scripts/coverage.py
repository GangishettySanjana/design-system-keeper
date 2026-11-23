#!/usr/bin/env python3
"""Check a design system against the ideal checklist (references/ideal-system.md) and say what it contains.

Usage:
  python coverage.py <tokens.json> [--docs <folder with the system's markdown/html docs>] [--out report.json]

Looks at the tokens file and, if given, every .md/.html/.json file in the docs folder (file names and text).
Each item is Found, Partly or Missing, with the evidence. Standard library only. Nothing is modified.
"""
import sys, os, re, json, argparse, glob

def read_docs(folder):
    text, names = '', []
    if folder and os.path.isdir(folder):
        for d, dirs, fs in os.walk(folder):
            dirs[:] = [x for x in dirs if x not in {'node_modules', '.git', '.next', 'dist', 'build', 'vendor', '.vercel'}]
            for f in fs:
                if f.lower().endswith(('.md', '.html', '.json', '.txt')):
                    p = os.path.join(d, f)
                    names.append(os.path.relpath(p, folder))
                    try:
                        text += '\n' + open(p, encoding='utf-8', errors='ignore').read()[:200000].lower()
                    except OSError:
                        pass
    return text, names

def has(text, names, *words):
    hits = [w for w in words if w in text or any(w in n.lower() for n in names)]
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tokens')
    ap.add_argument('--docs')
    ap.add_argument('--out')
    a = ap.parse_args()
    t = json.load(open(a.tokens))
    text, names = read_docs(a.docs)
    ctoks = (t.get('color') or {}).get('tokens', [])
    themes = [x.get('id') for x in (t.get('color') or {}).get('themes', [])]
    groups = (t.get('type') or {}).get('groups', [])
    nstyles = sum(len(g.get('styles', [])) for g in groups)
    sp = (t.get('spacing') or {}).get('tokens', [])
    rd = (t.get('radius') or {}).get('tokens', [])
    sh = (t.get('shadow') or {}).get('tokens', [])
    zi = (t.get('zindex') or {}).get('tokens', [])
    alltok = ctoks + sp + rd + sh + zi + [s for g in groups for s in g.get('styles', [])]
    with_use = [x for x in alltok if x.get('usage')]
    with_code = [x for x in alltok if 'code:' in str(x.get('usage', '')).lower()]
    comp_dirs = [n for n in names if n.lower().startswith('components/') and n.lower().endswith('readme.md')]
    comp_json = [n for n in names if n.lower().startswith('components/') and n.lower().endswith('.json')]
    S = lambda ok, part=None: 'Found' if ok else ('Partly' if part else 'Missing')

    rows = []
    def add(group, item, status, evidence):
        rows.append({'group': group, 'item': item, 'status': status, 'evidence': evidence})

    # Foundations
    add('Foundations', 'Colour', S(len(ctoks) >= 4), f'{len(ctoks)} colour tokens')
    add('Foundations', 'Typography', S(nstyles >= 4), f'{nstyles} text styles in {len(groups)} groups, families: {", ".join((t.get("type") or {}).get("families", {}).values()) or "none"}')
    add('Foundations', 'Spacing scale', S(len(sp) >= 4), f'{len(sp)} spacing tokens')
    add('Foundations', 'Corner radius', S(len(rd) >= 2), f'{len(rd)} radius tokens')
    add('Foundations', 'Elevation / shadows', S(len(sh) >= 1), f'{len(sh)} shadow tokens')
    add('Foundations', 'Layers (z-index)', S(len(zi) >= 1), f'{len(zi)} layer tokens')
    h = has(text, names, 'motion', 'animation', 'easing', 'duration')
    add('Foundations', 'Motion', S(h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    h = has(text, names, 'icon', 'iconograph')
    add('Foundations', 'Iconography', S(h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    h = has(text, names, 'logo', 'wordmark', 'brand')
    add('Foundations', 'Brand marks (logo, wordmark)', S(h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    h = has(text, names, 'photo', 'imagery', 'illustration')
    add('Foundations', 'Imagery and illustration', S(h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    # Token quality
    pct = int(100 * len(with_use) / len(alltok)) if alltok else 0
    add('Token quality', 'Every token has a usage note', 'Found' if pct == 100 else ('Partly' if pct >= 50 else 'Missing'), f'{pct}% of {len(alltok)} tokens')
    add('Token quality', 'Themes / modes', 'Found' if len(themes) >= 2 else ('Partly' if themes else 'Missing'), 'themes: ' + (', '.join(themes) or 'none'))
    add('Token quality', 'Code names linked to tokens', 'Found' if len(with_code) >= max(3, len(alltok) // 4) else ('Partly' if with_code else 'Missing'), f'{len(with_code)} tokens name their code variable')
    # Components
    ncomp = len(comp_dirs)
    add('Components', 'Components documented', 'Found' if ncomp >= 5 else ('Partly' if ncomp else 'Missing'), f'{ncomp} component pages')
    h = has(text, names, 'variant', 'states', 'props')
    add('Components', 'Variants, states and props described', S(len(h) >= 2, h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    add('Components', 'Live examples or previews', S(any(n.lower().endswith('preview.html') for n in names)), f'{sum(1 for n in names if n.lower().endswith("preview.html"))} preview pages')
    # Patterns
    h = has(text, names, 'pattern', 'template', 'layout', 'flow')
    add('Patterns', 'Patterns, templates and layouts', S(len(h) >= 2, h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    # Guidelines
    h = has(text, names, 'accessib', 'contrast', 'tap target', 'focus')
    add('Guidelines', 'Accessibility', S(len(h) >= 2, h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    h = has(text, names, 'voice', 'tone', 'writing', 'copy')
    add('Guidelines', 'Content and voice', S(len(h) >= 2, h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    h = has(text, names, 'principle', 'rules', 'hard rule')
    add('Guidelines', 'Principles and rules', S(len(h) >= 2, h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    h = has(text, names, 'condition', 'organizer', 'member', 'role')
    add('Guidelines', 'Conditions (what changes by role, device, theme, state)', S(len(h) >= 2, h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    # Documentation
    add('Documentation', 'Overview / README', S(any(n.lower().endswith('readme.md') and '/' not in n for n in names)), 'README.md at the top' if any(n.lower() == 'readme.md' for n in names) else 'no top-level README')
    h = has(text, names, 'decision', 'open item', 'changelog', 'change note')
    add('Documentation', 'Decisions ledger or change log', S(len(h) >= 1), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    # Governance
    h = has(text, names, 'governance', 'owner', 'contribut', 'review', 'keeping', 'process')
    add('Governance', 'Ownership and update process', S(len(h) >= 2, h), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    h = has(text, names, 'version', 'deprecat')
    add('Governance', 'Versioning and deprecation', S(len(h) >= 1), 'mentioned: ' + ', '.join(h) if h else 'nothing found')
    # AI readiness
    add('AI readiness', 'Machine-readable tokens', S(len(alltok) > 0), 'tokens.json with names, values and usage notes' if alltok else 'none')
    add('AI readiness', 'Machine-readable component data (JSON per component)', 'Found' if len(comp_json) >= max(1, ncomp // 2) and comp_json else ('Partly' if comp_json else 'Missing'), f'{len(comp_json)} component JSON files')
    h = [n for n in names if 'agents' in n.lower() or 'for-ai' in n.lower() or 'for_ai' in n.lower()]
    add('AI readiness', 'Always-on rules for AI agents (AGENTS.md or similar)', S(h), ', '.join(h) if h else 'no AGENTS.md or "for AI" page')
    pairs = sum(1 for x in alltok if re.search(r'[A-Z ]', str(x.get('name', ''))))
    add('AI readiness', 'Consistent token naming', 'Found' if pairs == 0 else 'Partly', 'lowercase, dash-separated names' if pairs == 0 else f'{pairs} names with capitals or spaces')

    order = {'Found': 2, 'Partly': 1, 'Missing': 0}
    score = sum(order[r['status']] for r in rows)
    mx = 2 * len(rows)
    print(f'# What this design system contains\n')
    print(f'Docs read: {len(names)} files' + (f' from {a.docs}' if a.docs else ' (no --docs folder given; only the tokens were checked)') + '.')
    if t.get('draft'):
        print('WARNING: these tokens are a DRAFT built from a scan of the code, not a design system a person made. The foundations below are what the code uses, not what was decided. Pass --docs only for a folder that really holds design-system documents; a project folder full of briefs and prompts will make the score look better than it is.\n')
    print(f'Overall: {score} of {mx} points ({int(100 * score / mx)}%). Found {sum(r["status"] == "Found" for r in rows)}, partly {sum(r["status"] == "Partly" for r in rows)}, missing {sum(r["status"] == "Missing" for r in rows)} of {len(rows)} checks.\n')
    g = None
    for r in rows:
        if r['group'] != g:
            g = r['group']; print(f'\n## {g}')
        mark = {'Found': '[x]', 'Partly': '[~]', 'Missing': '[ ]'}[r['status']]
        print(f'- {mark} {r["item"]}: {r["status"]}. {r["evidence"]}')
    if a.out:
        json.dump({'score': score, 'max': mx, 'rows': rows}, open(a.out, 'w'), indent=1)

if __name__ == '__main__':
    main()
