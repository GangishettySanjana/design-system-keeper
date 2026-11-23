#!/usr/bin/env python3
"""Check whether the code still matches the saved design system (a drift check you can run before each release).

Usage:
  python check_drift.py <tokens.json> <folder-or-label=folder> [more ...] [--min-uses 3] [--fail] [--write-names linked-tokens.json]

  Each source can be named, for example:  proto=./prototype  app=./app/src
  --min-uses N        ignore values used fewer than N times (default 3), so one-offs do not drown the report
  --fail              exit with code 1 when there is drift (use it in CI)
  --ignore HEXES      comma-separated colours to leave out, for example the prototype frame's own colours
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

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('tokens')
    ap.add_argument('sources', nargs='+')
    ap.add_argument('--min-uses', type=int, default=3)
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
    print(f'Saved system: {a.tokens} ({len(toks)} colour tokens). Ignoring values used fewer than {a.min_uses} times.\n')
    for label, path in src:
        C, n, _ = inv.scan([path])
        vars_ = inv.code_vars(C, None)
        new = {}
        for k in ('color', 'radius', 'font-size', 'spacing'):
            new[k] = [(v, c) for v, c in C[k].most_common() if c >= a.min_uses and (inv.norm_hex(v) if k == 'color' else v) not in tv[k] and (inv.norm_hex(v) if k == 'color' else v) not in ign]
        same_name = []
        for var, hexv, _ in vars_:
            nm = norm_name(var)
            if nm in by_name and hexv not in by_name[nm] and hexv not in ign:
                same_name.append((var, hexv, nm, by_name[nm]))
            for tokname, vs in by_name.items():
                if hexv in vs:
                    names[tokname][label].add(var)
                    if nm == tokname: exact[tokname][label].add(var)
        n_new = sum(len(x) for x in new.values())
        drift += n_new + len(same_name)
        print(f'## {label}  ({n} files)\n')
        print(f'- Used in the code but not in the tokens: {n_new} values')
        for k, lst in new.items():
            if lst: print(f'  - {k}: ' + ', '.join(f'{v} x{c}' for v, c in lst[:12]))
        print(f'- Same name, different value: {len(same_name)}')
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
        json.dump(t, open(a.write_names, 'w'), indent=2)
        print(f'\nWrote {a.write_names}')
    print(f'\n**Result: {"DRIFT" if drift else "IN STEP"}** ({drift} differences found).')
    if a.fail and drift: sys.exit(1)

if __name__ == '__main__':
    main()
