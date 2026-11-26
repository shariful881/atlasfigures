#!/usr/bin/env python3
"""Independent check of the city time pages (task 26).

Reads the BUILT pages in dist/time/<slug>/ and recomputes every table value with tools the site does not use:
  * Python zoneinfo (the system IANA tz database, here 2026e) instead of the browser/Node ICU copy;
  * astral (pip install astral) for sunrise, sunset and solar noon.
Checks: clock-change table (dates, times, offsets), sun table (21st of each month, ±2 min), time-difference table
(15 January and 15 July), the standard/daylight offsets in the facts box, and the WebPage/City JSON-LD coordinates.
Run after `npm run build`:  python3 scripts/verify/time-cities.py
"""
import json, re, sys, datetime as dt
from pathlib import Path
from zoneinfo import ZoneInfo
from html.parser import HTMLParser
from astral import Observer
from astral.sun import sun

DIST = Path('dist/time'); Y = 2026
UTC = dt.timezone.utc

class Tables(HTMLParser):
    def __init__(s): super().__init__(); s.tables=[]; s.cur=None; s.cell=None; s.row=None; s.dl=[]; s.indd=None; s.ld=[]; s.inld=False
    def handle_starttag(s,t,a):
        a=dict(a)
        if t=='table': s.cur=[]
        elif t=='tr' and s.cur is not None: s.row=[]
        elif t in('td','th') and s.row is not None: s.cell=''
        elif t in('dt','dd'): s.indd=[t,'']
        elif t=='script' and a.get('type')=='application/ld+json': s.inld=True; s.ldbuf=''
    def handle_endtag(s,t):
        if t in('td','th') and s.cell is not None: s.row.append(s.cell.strip()); s.cell=None
        elif t=='tr' and s.row is not None: s.cur.append(s.row); s.row=None
        elif t=='table': s.tables.append(s.cur); s.cur=None
        elif t in('dt','dd') and s.indd: s.dl.append((s.indd[0],s.indd[1].strip())); s.indd=None
        elif t=='script' and s.inld: s.ld.append(json.loads(s.ldbuf)); s.inld=False
    def handle_data(s,d):
        if s.cell is not None: s.cell+=d
        if s.indd: s.indd[1]+=d
        if s.inld: s.ldbuf+=d

def off(tz, when): return int(when.astimezone(ZoneInfo(tz)).utcoffset().total_seconds()//60)
def lab(m):
    a=abs(m); return f"UTC{'−' if m<0 else '+'}{a//60}" + (f":{a%60:02d}" if a%60 else '')
def transitions(tz, y0, y1):
    out=[]; t=dt.datetime(y0,1,1,tzinfo=UTC); end=dt.datetime(y1,1,1,tzinfo=UTC); prev=off(tz,t)
    while t<end:
        n=t+dt.timedelta(hours=1); cur=off(tz,n)
        if cur!=prev:
            lo,hi=t,n
            while (hi-lo)>dt.timedelta(minutes=1):
                mid=lo+(hi-lo)/2; mid=mid.replace(second=0,microsecond=0)
                if mid<=lo: break
                if off(tz,mid)==prev: lo=mid
                else: hi=mid
            out.append((hi,prev,cur)); prev=cur
        t=n
    return out

fails=0; checks=0
def ok(cond,msg):
    global fails,checks; checks+=1
    if not cond: fails+=1; print('  ✗',msg)

for f in sorted(Path('src/data/cities').glob('*.json')):
    c=json.loads(f.read_text()); slug=c['slug']; tz=c['tz']
    html=(DIST/slug/'index.html').read_text()
    p=Tables(); p.feed(html)
    print(f'{slug}:')
    trs=transitions(tz,Y,Y+2)
    tables=p.tables
    # tables: [changes?], sun, diff
    if trs:
        chg=tables[0][1:]; tables=tables[1:]
        ok(len(chg)==len(trs), f'changes rows {len(chg)} ≠ {len(trs)}')
        for row,(at,b,a) in zip(chg,trs):
            loc=at.astimezone(ZoneInfo(tz))
            want_date=f"{loc.strftime('%A')}, {loc.day} {loc.strftime('%B %Y')}"
            frm=(at+dt.timedelta(minutes=b)).strftime('%H:%M'); to=(at+dt.timedelta(minutes=a)).strftime('%H:%M')
            ok(row[0]==want_date, f'change date {row[0]} ≠ {want_date}')
            ok(row[1]==('forward' if a>b else 'back'), f'direction {row[1]}')
            ok(row[2]==f'{frm} → {to}', f'change time {row[2]} ≠ {frm} → {to}')
            ok(row[3]==lab(a), f'new offset {row[3]} ≠ {lab(a)}')
    else:
        ok(len(tables)==2, 'city without daylight saving should have no clock-change table')
    sunt=tables[0][1:]; ok(len(sunt)==12,'sun table rows')
    obs=Observer(latitude=c['lat'],longitude=c['lon'])
    for m,row in enumerate(sunt,1):
        s=sun(obs,date=dt.date(Y,m,21),tzinfo=ZoneInfo(tz))
        for col,key in ((1,'sunrise'),(2,'noon'),(3,'sunset')):
            h,mi=map(int,row[col].split(':')); ref=s[key]; diff=abs((h*60+mi)-(ref.hour*60+ref.minute+ref.second/60))
            ok(diff<=2, f'{key} 21/{m}: {row[col]} vs astral {ref.strftime("%H:%M:%S")}')
        L=(s['sunset']-s['sunrise']).total_seconds()/60
        hh,mm=map(int,re.findall(r'\d+',row[4])); ok(abs(hh*60+mm-L)<=2, f'day length 21/{m}: {row[4]} vs {L:.1f} min')
    others={json.loads(g.read_text())['name']:json.loads(g.read_text())['tz'] for g in Path('src/data/cities').glob('*.json') if g!=f}
    jan=dt.datetime(Y,1,15,12,tzinfo=UTC); jul=dt.datetime(Y,7,15,12,tzinfo=UTC)
    def d(o,w):
        m=off(o,w)-off(tz,w)
        if m==0: return 'Same time'
        a=abs(m); return f"{'+' if m>0 else '−'}{a//60}"+(f":{a%60:02d}" if a%60 else '')+' h'
    for row in tables[1][1:]:
        o=others[row[0]]; ok(row[1]==d(o,jan) and row[2]==d(o,jul), f'diff {row[0]}: {row[1]}/{row[2]} ≠ {d(o,jan)}/{d(o,jul)}')
    ok(len(tables[1])-1==len(others),'diff table covers every other city')
    facts=dict((p.dl[i][1],p.dl[i+1][1]) for i in range(0,len(p.dl)-1,2) if p.dl[i][0]=='dt')
    offs=sorted({off(tz,dt.datetime(Y,1,1,tzinfo=UTC))}|{a for _,_,a in transitions(tz,Y,Y+1)})
    ok(facts.get('Time zone')==tz, 'facts: time zone')
    ok(facts.get('Standard time','').startswith(lab(offs[0])), f"facts: standard {facts.get('Standard time')} ≠ {lab(offs[0])}")
    ok((facts.get('Daylight saving')=='Not used') == (len(offs)==1), 'facts: daylight saving')
    if len(offs)>1: ok(facts['Daylight saving'].startswith(lab(offs[-1])), 'facts: daylight offset')
    graph=[n for g in p.ld for n in g.get('@graph',[])]
    city=[n['about'] for n in graph if n.get('@type')=='WebPage'][0]
    ok(city['geo']['latitude']==c['lat'] and city['geo']['longitude']==c['lon'], 'JSON-LD coordinates')

print('historical claims in the text:')
U=lambda *a: dt.datetime(*a,tzinfo=UTC)
ok(off('Asia/Dhaka',U(2009,8,1))==420 and off('Asia/Dhaka',U(2009,6,1))==360 and off('Asia/Dhaka',U(2010,1,2))==360, 'Dhaka on UTC+7 for part of 2009 only')
ok(all(off('Asia/Dhaka',U(y,m,1))==360 for y in range(1952,Y+1) for m in (1,7) if y!=2009), 'Dhaka UTC+6 every other year since 1952')
ok(off('Europe/London',U(1969,1,15))==60 and off('Europe/London',U(1970,12,15))==60 and off('Europe/London',U(1972,1,15))==0, 'London UTC+1 all year 1968-71')
ok(off('Asia/Tokyo',U(1949,7,1))==600 and all(off('Asia/Tokyo',U(y,7,1))==540 for y in range(1952,Y+1)), 'Tokyo summer time 1948-51 only')
ok(off('Asia/Singapore',U(1981,12,31,12))==450 and off('Asia/Singapore',U(1982,1,2))==480, 'Singapore UTC+7:30 to UTC+8 at the start of 1982')
ok(off('Asia/Kolkata',U(1943,7,1))==390 and all(off('Asia/Kolkata',U(y,m,1))==330 for y in range(1946,Y+1) for m in (1,7)), 'India UTC+6:30 in wartime, UTC+5:30 since')
ok(all(off('Asia/Dubai',U(y,m,1))==240 for y in range(1921,Y+1) for m in (1,7)), 'Dubai UTC+4 since 1920')
ok(all(off('Europe/Paris',U(y,1,15))==60 for y in range(1946,Y+1)) and off('Europe/Paris',U(1939,12,15))==0, 'Paris UTC+1 every winter since 1946, UTC+0 before 1940')
ny6=[t for t in transitions('America/New_York',2006,2008)]
ok(ny6[0][0].month==4 and ny6[2][0].month==3 and ny6[3][0].month==11, 'US daylight time moved from April to March in 2007')
print(f'\n{checks} checks, {fails} failed'); sys.exit(1 if fails else 0)
