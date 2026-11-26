#!/usr/bin/env python3
"""Build src/data/tz-country.json: IANA time zone name -> ISO 3166 alpha-2 country code.

Used only by the home page's "Your country" card, which guesses a visitor's country from the device time zone
(nothing is sent anywhere). Source: IANA tz database files zone.tab (zone -> country) and tzdata.zi
(link lines "L target alias", so old names browsers still report, e.g. Asia/Calcutta, also resolve).
Run: python3 scripts/build-tz-country.py [/usr/share/zoneinfo]
"""
import json, sys, os
src = sys.argv[1] if len(sys.argv) > 1 else '/usr/share/zoneinfo'
zones = {}
for line in open(os.path.join(src, 'zone.tab'), encoding='utf-8'):
    if line.startswith('#') or not line.strip():
        continue
    cc, _coord, tz = line.split('\t')[:3]
    zones[tz.strip()] = cc
version = None
links = {}
for line in open(os.path.join(src, 'tzdata.zi'), encoding='utf-8'):
    if line.startswith('# version'):
        version = line.split()[-1]
    if line.startswith('L '):
        _, target, alias = line.split()
        links[alias] = target
for alias, target in links.items():
    t = target
    for _ in range(5):
        if t in zones:
            zones.setdefault(alias, zones[t])
            break
        t = links.get(t, t)
out = {'source': f'IANA tz database {version} (zone.tab + links in tzdata.zi)', 'zones': dict(sorted(zones.items()))}
json.dump(out, open('src/data/tz-country.json', 'w'), ensure_ascii=False, separators=(',', ':'))
print(version, len(zones), 'zones')
