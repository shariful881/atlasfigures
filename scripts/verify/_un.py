# Shared reader for the per-country verification scripts (scripts/verify/<slug>.py).
# Reads the ORIGINAL UN files directly (never the site's generated src/data/wpp/), so a bug in
# scripts/build-data.mjs cannot hide behind itself. Needs: pip install openpyxl
import gzip, csv, re, json, html, io, zipfile, openpyxl

WPP = 'data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz'
UPD = 'data/raw/un-wpp-2024/WPP2024_CSV_files_update.zip'
WUP = 'data/raw/un-wup-2025/WUP2025-F15-National-Definitions_percPop_by_category.xlsx'

raw = {}   # ISO3 -> year -> row (countries/areas only), plus 'WORLD'
def _add(r):
    if r['Variant'] != 'Medium': return
    if r['Location'] == 'World': raw.setdefault('WORLD', {})[int(r['Time'])] = r
    elif r['LocTypeName'] == 'Country/Area' and r['ISO3_code']: raw.setdefault(r['ISO3_code'], {})[int(r['Time'])] = r
with gzip.open(WPP, 'rt', encoding='utf-8-sig') as f:
    for r in csv.DictReader(f): _add(r)
with zipfile.ZipFile(UPD) as z:   # interim update replaces whole countries
    for n in z.namelist():
        if 'Demographic_Indicators' in n and n.endswith('.csv'):
            upd = {}
            for r in csv.DictReader(io.TextIOWrapper(z.open(n), encoding='utf-8-sig')):
                if r['Variant'] == 'Medium' and r['LocTypeName'] == 'Country/Area' and r['ISO3_code']:
                    upd.setdefault(r['ISO3_code'], {})[int(r['Time'])] = r
            raw.update(upd)

wb = openpyxl.load_workbook(WUP, read_only=True, data_only=True)
_rows = list(wb['Urban'].iter_rows(values_only=True)); _h = _rows[0]
def urban(iso):
    row = [r for r in _rows if r[4] == iso][0]
    return {int(_h[i]): row[i] for i in range(10, len(_h)) if _h[i] and str(_h[i]).isdigit()}

def f(iso, y, col): return float(raw[iso][y][col])
def P(iso, y): return round(f(iso, y, 'TPopulation1July') * 1000)
def K(iso, y, col): return round(f(iso, y, col) * 1000)          # thousands -> people
def rank(iso, y):
    pops = sorted(((float(v[y]['TPopulation1July']), k) for k, v in raw.items() if k != 'WORLD' and y in v and v[y]['TPopulation1July']), reverse=True)
    return [k for _, k in pops].index(iso) + 1
def land(iso): return P(iso, 2023) / f(iso, 2023, 'PopDensity')

c = lambda n: f"{round(n):,}"
m = lambda n: f"{n/1e6:.1f} million"
b2 = lambda n: f"{n/1e9:.2f} billion"
p1 = lambda v: f"{v:.1f}%"
def ordn(n): return f"{n}{'th' if 11 <= n % 100 <= 13 else {1:'st',2:'nd',3:'rd'}.get(n % 10, 'th')}"

def load_page(slug):
    page = open(f'dist/population/{slug}/index.html').read()
    text = html.unescape(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', re.sub(r'<script.*?</script>|<style.*?</style>', '', page, flags=re.S))))
    ld = html.unescape(' '.join(re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)))
    return page, text, ld

def run(slug, iso, exp, ld_keys, table_years):
    page, text, ld = load_page(slug)
    U = urban(iso)
    bad = 0
    for k, v in exp.items():
        ok = v in text; bad += not ok
        print('OK  ' if ok else 'MISS', k, '=', v)
    for k in ld_keys:
        v = exp[k]; ok = v in ld; bad += not ok
        print('OK  ' if ok else 'MISS', 'JSON-LD has', k, '=', v)
    for yr in table_years:
        v = c(P(iso, yr)); ok = v in text; bad += not ok
        print('OK  ' if ok else 'MISS', 'table', yr, v)
    csvt = open(f'dist/data/{slug}-population.csv').read()
    for yr in table_years:
        line = [l for l in csvt.splitlines() if l.startswith(f'{yr},')][0].split(',')
        urb = '' if yr not in U or U[yr] is None or yr > 2050 else round(U[yr], 1)
        good = (int(line[1]) == P(iso, yr) and line[2] == str(round(f(iso, yr, 'PopDensity')))
                and float(line[3]) == round(f(iso, yr, 'TFR'), 2) and float(line[4]) == round(f(iso, yr, 'MedianAgePop'), 1)
                and (line[5] == '' if urb == '' else float(line[5]) == urb)
                and int(line[6]) == K(iso, yr, 'NetMigrations') and int(line[7]) == rank(iso, yr))
        bad += not good; print('OK  ' if good else 'MISS', 'CSV row', yr)
    live = f'data-anchor="{P(iso, 2026)}"' in page and f'data-rate="{K(iso, 2026, "PopChange")}"' in page and 'data-date="2026-07-01"' in page
    bad += not live; print('OK  ' if live else 'MISS', 'live counter anchor/rate/date')
    print(f'\nRESULT {slug}:', 'ALL MATCH' if not bad else f'{bad} mismatches', f'({len(exp) + len(ld_keys) + 2 * len(table_years) + 1} checks)')
    return bad
