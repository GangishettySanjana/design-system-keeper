#!/usr/bin/env python3
"""Check whether the code still matches the saved design system (a drift check you can run before each release).

Usage:
  python check_drift.py <tokens.json> <folder-or-label=folder> [more ...] [--min-uses 3] [--fail] [--write-names linked-tokens.json]

  Each source can be named, for example:  proto=./prototype  app=./app/src
  --min-uses N        ignore values used fewer than N times. Automatic by default: a small project (40 colours or fewer)
                      checks every value; a larger one ignores values used fewer than 3 times so one-offs do not drown the report
  --fail              exit with code 1 when there is drift (use it in CI)
  --ignore HEXES      comma-separated hex values to leave out. Give the exact colours of the prototype frame's own variables (the ledger's "skipped" pile)
  --write-names FILE  write a copy of tokens.json where every colour token lists the code variable that holds
                      its value, per source: "code": {"proto": ["--t-ink"], "app": ["--text"]}

Reports, per source: values used in the code but not in the tokens, variables that share a token's name but
hold a different value, and which code variable names map to each token. The project is only read.
Standard library only.
"""
import sys, os, re, json, argparse, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import inventory as inv

def norm_name(v):
    v = v.lstrip('-')
    for p in ('color-', 'colour-', 'c-', 't-'):
        if v.startswith(p): v = v[len(p):]
    return v

def tokval(tok, th):
    """The token's value for a theme. A token with a single value applies to light only."""
    v = tok['value']
    if isinstance(v, dict): return v.get(th)
    return v if th == 'light' else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tokens')
    ap.add_argument('sources', nargs='+')
    ap.add_argument('--min-uses', type=int, default=None)
    ap.add_argument('--fail', action='store_true')
    ap.add_argument('--write-names')
    ap.add_argument('--ignore', default='')
    a = ap.parse_args()
    t = json.load(open(a.tokens))
    tv = inv.token_values(a.tokens)
    ign = {inv.norm_hex(x.strip()) for x in a.ignore.split(',') if x.strip()}
    toks = (t.get('color') or {}).get('tokens', [])
    def values(tok):
        v = tok['value']
        vs = [inv.norm_hex(x) for x in (v.values() if isinstance(v, dict) else [v]) if isinstance(x, str) and x.startswith('#')]
        return vs
    by_name = {tok['name']: values(tok) for tok in toks}
    src = []
    for s in a.sources:
        label, _, path = s.partition('=') if '=' in s else (os.path.basename(s.rstrip('/')), '', s)
        src.append((label, path))
    drift, names = 0, collections.defaultdict(lambda: collections.defaultdict(set))
    exact = collections.defaultdict(lambda: collections.defaultdict(set))
    print('# Drift check\n')
    print(f'Saved system: {a.tokens} ({len(toks)} colour tokens).\n')
    total_low = 0
    for label, path in src:
        inv.THEME_VARS.clear(); inv.THEME_MULTI.clear()
        C, n, _ = inv.scan([path])
        mu = a.min_uses or (1 if len(C['color']) <= 40 else 3)
        vars_ = inv.code_vars(C, None)
        new = {}
        for k in ('color', 'radius', 'font-size', 'spacing'):
            new[k] = [(v, c) for v, c in C[k].most_common() if c >= mu and (inv.norm_hex(v) if k == 'color' else v) not in tv[k] and (inv.norm_hex(v) if k == 'color' else v) not in ign]
        same_name = []
        for var, hexv, _ in vars_:
            nm = norm_name(var)
            for tokname, vs in by_name.items():
                if hexv in vs:
                    names[tokname][label].add(var)
                    if nm == tokname: exact[tokname][label].add(var)
        tokmap = {tok['name']: tok for tok in toks}
        for var, dd in inv.THEME_MULTI.items():
            nm = norm_name(var)
            if nm not in tokmap: continue
            for th, vals in dd.items():
                tvl = tokval(tokmap[nm], th)
                if tvl is None: continue
                for hv in sorted(vals):
                    if inv.norm_hex(hv) != inv.norm_hex(tvl) and inv.norm_hex(hv) not in ign:
                        same_name.append((var + ' (' + th + ')', hv, nm, [tvl.lower()]))
        multi = []
        for var, dd in inv.THEME_MULTI.items():
            for th, vals in dd.items():
                vals = sorted(v for v in vals if v not in ign)
                if len(vals) > 1: multi.append((var, th, vals))
        n_new = sum(len(x) for x in new.values())
        low = sum(1 for k in ('color', 'radius', 'font-size', 'spacing') for v, c in C[k].items() if c < mu and (inv.norm_hex(v) if k == 'color' else v) not in tv[k])
        total_low += low
        drift += n_new + len(same_name) + len(multi)
        print(f'## {label}  ({n} files)\n')
        print(f'- Checked values used {mu} or more times ({"automatic" if not a.min_uses else "set by --min-uses"}); {low} rarer values were not checked.')
        print(f'- Used in the code but not in the tokens: {n_new} values')
        for k, lst in new.items():
            if lst: print(f'  - {k}: ' + ', '.join(f'{v} x{c}' for v, c in lst[:12]))
        print(f'- Defined more than once with different values: {len(multi)}  (the app can show two different colours for the same name)')
        for var, th, vals in multi[:12]:
            print(f'  - `{var}` in the {th} theme: ' + ', '.join(vals))
        print(f'- Same name as a token, different value (compared theme by theme): {len(same_name)}')
        for var, hexv, nm, vs in same_name[:15]:
            print(f'  - `{var}` is {hexv} in the code, but token `{nm}` is {", ".join(vs)}')
        print()
    def best(tokname):
        """Variables with the token's own name win; otherwise up to 3 that only share the value."""
        return {lb: (sorted(exact[tokname][lb]) if exact[tokname].get(lb) else sorted(v)[:3]) for lb, v in names[tokname].items()}
    linked = sum(1 for tok in toks if names.get(tok['name']))
    print(f'## Names linked\n\n{linked} of {len(toks)} colour tokens have a code variable in at least one source. A variable with the same name as the token is shown when there is one; otherwise up to 3 that hold the same value.')
    for tok in toks[:60]:
        if names.get(tok['name']):
            print(f'- `{tok["name"]}`: ' + '; '.join(lb + ': ' + ', '.join('`' + x + '`' for x in v) for lb, v in best(tok['name']).items()))
    if a.write_names:
        for tok in (t.get('color') or {}).get('tokens', []):
            if names.get(tok['name']):
                tok['code'] = best(tok['name'])
                ex = {lb: sorted(v) for lb, v in exact[tok['name']].items() if v}
                if ex: tok['code_exact'] = ex
        json.dump(t, open(a.write_names, 'w'), indent=2)
        print(f'\nWrote {a.write_names}')
    print(f'\n**Result: {"DRIFT" if drift else "IN STEP"}** ({drift} differences found at this threshold; {total_low} rarer values were not checked). The exit code is 0 unless --fail is given.')
    if a.fail and drift: sys.exit(1)

if __name__ == '__main__':
    main()
