# Shared helpers for the independent verify scripts (task 149). Reads the ORIGINAL World Bank zips in
# data/raw/wdi/ — never the site's generated data. Same claim helpers as src/lib/claims.ts, same rules.
#   import sys; sys.path.insert(0, 'scripts/verify'); from _wdi import *
#   GDP = wdi('NY.GDP.MKTP.CD'); claim('bangladesh', 'remittances record', highest_since(REM['BGD'], 2025) is None)
import csv, io, zipfile, re, html

_meta = {}

def wdi(code):
    """{iso3: {year: value}} for one indicator (countries and aggregates). Country metadata goes to ECON."""
    with zipfile.ZipFile(f'data/raw/wdi/{code}.zip') as z:
        n = z.namelist()
        lines = z.read([x for x in n if x.startswith('API_')][0]).decode('utf-8-sig').splitlines()
        meta = list(csv.DictReader(io.StringIO(z.read([x for x in n if x.startswith('Metadata_Country')][0]).decode('utf-8-sig'))))
    for m in meta:
        if m['Region']:
            _meta[m['Country Code']] = m
    i = next(k for k, l in enumerate(lines) if l.startswith('"Country Name"'))
    return {r['Country Code']: {int(k): float(v) for k, v in r.items() if k and k.isdigit() and v not in ('', None)}
            for r in csv.DictReader(io.StringIO('\n'.join(lines[i:])))}

ECON = _meta  # iso3 -> World Bank country metadata (Region, IncomeGroup); filled by wdi()

# ---- claim helpers (mirror src/lib/claims.ts) -------------------------------------------------------
def highest_since(s, year):
    v = s[year]; prev = [y for y in s if y < year and s[y] >= v]
    return max(prev) if prev else None

def lowest_since(s, year):
    v = s[year]; prev = [y for y in s if y < year and s[y] <= v]
    return max(prev) if prev else None

def streak(s):
    ys = sorted(s)
    if len(ys) < 2: return ('flat', 0, ys[-1] if ys else 0)
    sg = lambda i: (s[ys[i]] > s[ys[i - 1]]) - (s[ys[i]] < s[ys[i - 1]])
    d = sg(len(ys) - 1); i = len(ys) - 1
    while i > 0 and ys[i] - ys[i - 1] == 1 and sg(i) == d and d != 0: i -= 1
    return ('up' if d > 0 else 'down' if d < 0 else 'flat', len(ys) - 1 - i, ys[i])

def above_since(s, t):
    ys = sorted(s)
    if not ys or s[ys[-1]] <= t: return None
    i = len(ys) - 1
    while i > 0 and s[ys[i - 1]] > t: i -= 1
    return ys[i]

def below_since(s, t):
    ys = sorted(s)
    if not ys or s[ys[-1]] >= t: return None
    i = len(ys) - 1
    while i > 0 and s[ys[i - 1]] < t: i -= 1
    return ys[i]

def times(s, y0, y1): return s[y1] / s[y0]

def latest(s): y = max(s); return y, s[y]

def rank_latest(src, iso, since, keep=lambda k: True, lowest_first=False):
    """Position among countries (not aggregates) by each one's latest value from `since` on, like rankLatest."""
    vals = {k: v[max(y for y in v if y >= since)] for k, v in src.items() if k in ECON and keep(k) and any(y >= since for y in v)}
    order = sorted(vals.items(), key=lambda kv: ((kv[1] if lowest_first else -kv[1]), kv[0]))
    return [k for k, _ in order].index(iso) + 1, len(order)

def rank_in(src, iso, year, keep=lambda k: True):
    """Position among countries with a value in `year`, highest first, like rankBy."""
    order = sorted([(k, v[year]) for k, v in src.items() if k in ECON and keep(k) and year in v], key=lambda kv: (-kv[1], kv[0]))
    return [k for k, _ in order].index(iso) + 1, len(order)

region = lambda r: (lambda k: ECON[k]['Region'] == r)

# ---- page reading and scoring ----------------------------------------------------------------------
ok = 0; bad = []

def page_text(path):
    p = open(path, encoding='utf-8').read()
    t = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', p, flags=re.S))))
    return p, t

def expect(t, slug, d):
    global ok
    for k, v in d.items():
        if v in t: ok += 1
        else: bad.append(f'{slug}: {k} {v!r} not on the page')

def claim(slug, k, c):
    global ok
    if c: ok += 1
    else: bad.append(f'{slug}: claim false: {k}')

def report():
    print(f'{ok} checks passed')
    for b in bad: print('FAIL', b)
    raise SystemExit(1 if bad else 0)

# number style (data guide)
usd = lambda v: f"${v/1e12:.2f} trillion" if v >= 1e12 else f"${v/1e9:.1f} billion" if v >= 1e9 else f"${v/1e6:.1f} million" if v >= 1e6 else f"${round(v):,}"
whole = lambda v: f"${round(v):,}"
p1 = lambda v: f"{v:.1f}%"
ordn = lambda n: f"{n}{'th' if 10 <= n % 100 <= 20 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')}"
