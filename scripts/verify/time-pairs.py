#!/usr/bin/env python3
"""Independent check of the two-city time pages (task 27), e.g. dist/time/dhaka-to-london/.

Recomputes with Python zoneinfo (system IANA tz, here 2026e), not the ICU copy used to build the site:
  * hour table: every whole hour in city A on 15 January and 15 July 2026 converted to city B (with next/previous day);
  * gap table: periods of 2026 with the same gap (changeover-night blips shorter than a day folded in, as on the page);
  * facts box: January/July gaps and shared 09:00-17:00 office hours.
Run after `npm run build`:  python3 scripts/verify/time-pairs.py
"""
import json, sys, datetime as dt, importlib.util
from pathlib import Path
from zoneinfo import ZoneInfo
src = Path(__file__).with_name('time-cities.py').read_text().split("fails=0; checks=0")[0]
ns = {}; exec(src, ns)          # reuse the HTML table parser and transition finder, without running the city checks
Tables, off, transitions = ns['Tables'], ns['off'], ns['transitions']
UTC = dt.timezone.utc; Y = 2026
fails = 0; checks = 0
def ok(c, m):
    global fails, checks; checks += 1
    if not c: fails += 1; print('  ✗', m)
def gaptxt(m):
    return 'Same time' if m == 0 else f"{'+' if m > 0 else '−'}{abs(m)//60}" + (f":{abs(m)%60:02d}" if abs(m) % 60 else '') + ' h'
def ext(m):
    h, r = abs(m)//60, abs(m) % 60
    return ' '.join(x for x in [f'{h} h' if h else '', f'{r} min' if r else ''] if x) or '0 h'
cities = {json.loads(f.read_text())['slug']: json.loads(f.read_text()) for f in Path('src/data/cities').glob('*.json')}
for f in sorted(Path('src/data/pairs').glob('*.json')):
    p = json.loads(f.read_text()); A, B = cities[p['a']], cities[p['b']]
    print(p['slug'] + ':')
    h = Tables(); h.feed((Path('dist/time') / p['slug'] / 'index.html').read_text())
    hours, per = h.tables[0][1:], h.tables[1][1:]
    for ref_day, col in ((dt.date(Y, 1, 15), 1), (dt.date(Y, 7, 15), 2)):
        for hr, row in enumerate(hours):
            t = dt.datetime(ref_day.year, ref_day.month, ref_day.day, hr, tzinfo=ZoneInfo(A['tz']))
            bt = t.astimezone(ZoneInfo(B['tz']))
            shift = (bt.date() - t.date()).days
            want = bt.strftime('%H:%M') + (' (next day)' if shift > 0 else ' (previous day)' if shift < 0 else '')
            ok(row[0] == f'{hr:02d}:00' and row[col] == want, f'{ref_day} {hr:02d}:00 → {row[col]} ≠ {want}')
    # gap periods
    s, e = dt.datetime(Y, 1, 1, tzinfo=UTC), dt.datetime(Y + 1, 1, 1, tzinfo=UTC)
    cuts = sorted([t for t, _, _ in transitions(A['tz'], Y, Y + 1)] + [t for t, _, _ in transitions(B['tz'], Y, Y + 1)])
    pts = [s] + cuts + [e]; raw = []
    for i in range(len(pts) - 1):
        g = off(B['tz'], pts[i] + dt.timedelta(seconds=1)) - off(A['tz'], pts[i] + dt.timedelta(seconds=1))
        if raw and raw[-1][2] == g: raw[-1][1] = pts[i + 1]
        else: raw.append([pts[i], pts[i + 1], g])
    seasons = []
    for x in [r for r in raw if r[1] - r[0] >= dt.timedelta(days=1)]:
        if seasons and seasons[-1][2] == x[2]: seasons[-1][1] = x[1]
        else:
            if seasons: seasons[-1][1] = x[0]
            seasons.append(list(x))
    ok(len(per) == len(seasons), f'gap periods {len(per)} ≠ {len(seasons)}')
    fmt = lambda t: f"{t.astimezone(ZoneInfo(A['tz'])).day} {t.astimezone(ZoneInfo(A['tz'])).strftime('%B')}"
    for i, (row, (a0, a1, g)) in enumerate(zip(per, seasons)):
        ok(row[0] == ('1 January' if i == 0 else fmt(a0)), f'period start {row[0]}')
        ok(row[1] == ('31 December' if i == len(seasons) - 1 else fmt(a1)), f'period end {row[1]}')
        ok(row[2] == gaptxt(g), f'period gap {row[2]} ≠ {gaptxt(g)}')
    facts = dict((h.dl[i][1], h.dl[i + 1][1]) for i in range(0, len(h.dl) - 1, 2) if h.dl[i][0] == 'dt')
    for label, day in (('January', dt.datetime(Y, 1, 15, 12, tzinfo=UTC)), ('July', dt.datetime(Y, 7, 15, 12, tzinfo=UTC))):
        g = off(B['tz'], day) - off(A['tz'], day)
        want = f"{B['name']} " + ('same time' if g == 0 else f"{ext(g)} {'ahead' if g > 0 else 'behind'}")
        ok(facts.get(f'Gap in mid-{label}') == want, f'facts gap {label}: {facts.get(f"Gap in mid-{label}")} ≠ {want}')
        lo, hi = max(540, 540 - g), min(1020, 1020 - g)
        want = f"{lo//60:02d}:{lo%60:02d}–{hi//60:02d}:{hi%60:02d} in {A['name']} ({ext(hi-lo)})" if hi > lo else 'No overlap'
        ok(facts.get(f'Shared office hours, {label}') == want, f'office {label}: {facts.get(f"Shared office hours, {label}")} ≠ {want}')
print(f'\n{checks} checks, {fails} failed'); sys.exit(1 if fails else 0)
