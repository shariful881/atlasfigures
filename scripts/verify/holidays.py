#!/usr/bin/env python3
"""Independent check of the Bangladesh holiday page and countdown (task 28).

Compares the BUILT page, CSV and calendar file with src/data/holidays/bangladesh-2027.json, recomputes every weekday
with Python's datetime, the weekend counts reported by the cabinet (4 general + 3 executive on Friday/Saturday),
the long breaks, and the Umm al-Qura dates with the hijridate library (pip install hijridate) instead of the
JavaScript (CLDR) calendar the site uses. Run after `npm run build`:  python3 scripts/verify/holidays.py
"""
import json, csv, re, sys, datetime as dt
from pathlib import Path
from hijridate import Hijri
data = json.loads(Path('src/data/holidays/bangladesh-2027.json').read_text())
H = sorted(data['holidays'], key=lambda h: (h['date'], h['type']))
fails = checks = 0
def ok(c, m):
    global fails, checks; checks += 1
    if not c: fails += 1; print('  ✗', m)
D = lambda s: dt.date.fromisoformat(s)
wk = lambda s: D(s).weekday() in (4, 5)  # Friday, Saturday
r = data['reported']
ok(len(H) == r['total'], 'total')
ok(sum(h['type'] == 'general' for h in H) == r['general'] and sum(h['type'] == 'executive' for h in H) == r['executive'], 'general/executive counts')
ok(sum(wk(h['date']) and h['type'] == 'general' for h in H) == r['onWeekendGeneral'], 'general on weekend')
ok(sum(wk(h['date']) and h['type'] == 'executive' for h in H) == r['onWeekendExecutive'], 'executive on weekend')
html = re.sub(r' data-astro-cid-\w+(="[^"]*")?', '', Path('dist/holidays/bangladesh/2027/index.html').read_text())
rows = re.findall(r'<tr data-date="([\d-]+)"[^>]*>\s*<th scope="row">([^<]+)<span class="wd-m">[^<]*</span></th>\s*<td>([^<]+)</td>\s*<td class="hn">(.*?)</td>\s*<td><span class="tag (\w+)">', html)
ok(len(rows) == len(H), f'page rows {len(rows)}')
for (d, ds, wd, name, typ), h in zip(rows, H):
    ok(d == h['date'] and typ == h['type'], f'row {d} {typ}')
    ok(wd.replace(' (weekend)', '') == D(d).strftime('%A') and (('(weekend)' in wd) == wk(d)), f'weekday {d}: {wd}')
    ok(ds == f"{D(d).day} {D(d).strftime('%B')}", f'date text {ds}')
    ok(re.sub('<[^>]+>', '', name).startswith(h['name']), f'name {d}')
c = list(csv.DictReader(open('dist/data/bangladesh-holidays-2027.csv')))
ok([(x['date'], x['holiday'], x['type']) for x in c] == [(h['date'], h['name'], h['type']) for h in sorted(data['holidays'], key=lambda h: h['date'])], 'CSV = data')
ics = Path('dist/data/bangladesh-holidays-2027.ics').read_text()
ok(sorted(re.findall(r'DTSTART;VALUE=DATE:(\d{8})', ics)) == sorted(h['date'].replace('-', '') for h in H), 'calendar file dates')
# long breaks (holidays + Friday/Saturday)
off = {h['date'] for h in H}
d = dt.date(2027, 1, 1); runs = []
while d.year == 2027:
    if d.isoformat() in off or d.weekday() in (4, 5):
        e = d
        while e.isoformat() in off or e.weekday() in (4, 5): e += dt.timedelta(days=1)
        n = (e - d).days
        if n >= 3 and any(x.isoformat() in off for x in (d + dt.timedelta(days=i) for i in range(n))): runs.append((d, n))
        d = e
    else: d += dt.timedelta(days=1)
longest = max(runs, key=lambda x: x[1])
ok(f"<dt>Longest break</dt><dd>{longest[1]} days, {longest[0].day} {longest[0].strftime('%B')}" in html, f'longest break {longest}')
ok(len(re.findall(r'<ul class="breaks">(.*?)</ul>', html, re.S)[0].split('<li>')) - 1 == len(runs), f'number of breaks {len(runs)}')
# Umm al-Qura comparison dates
fitr = Hijri(1448, 10, 1).to_gregorian(); azha = Hijri(1448, 12, 10).to_gregorian(); ram = Hijri(1448, 9, 1).to_gregorian()
ok(f"Umm al-Qura calendar: {fitr.day} {fitr.strftime('%B')}" in html and f"Umm al-Qura calendar: {azha.day} {azha.strftime('%B')}" in html, f'Umm al-Qura Eids {fitr} {azha}')
cd = re.sub(r' data-astro-cid-\w+(="[^"]*")?', '', Path('dist/countdown/eid-ul-fitr/index.html').read_text())
eid = next(h['date'] for h in H if h['name'] == 'Eid-ul-Fitr')
ok(f'data-target="{eid}T00:00:00+06:00"' in cd, 'countdown target = list date')
ok(f"{ram.strftime('%A')}, {ram.day} {ram.strftime('%B')} 2027" in cd, f'Ramadan start {ram}')
print(f'{checks} checks, {fails} failed'); sys.exit(1 if fails else 0)
