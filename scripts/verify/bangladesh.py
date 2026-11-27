# Run after `npm run build`: python3 scripts/verify/bangladesh.py  (needs: pip install openpyxl)
# Independent check: read the ORIGINAL UN files (not the site's generated data) and confirm every
# figure shown on the built Bangladesh page, CSV and home page.
import gzip, csv, io, re, json, html, openpyxl
raw={}
with gzip.open('data/raw/un-wpp-2024/WPP2024_Demographic_Indicators_Medium.csv.gz','rt',encoding='utf-8-sig') as f:
    for r in csv.DictReader(f):
        if r['ISO3_code']=='BGD' or r['Location']=='World' or r['LocTypeName']=='Country/Area': raw.setdefault(r['Location'],{})[int(r['Time'])]=r
B={y:r for y,r in raw['Bangladesh'].items()}; W=raw['World']
wb=openpyxl.load_workbook('data/raw/un-wup-2025/WUP2025-F15-National-Definitions_percPop_by_category.xlsx',read_only=True,data_only=True)
rows=list(wb['Urban'].iter_rows(values_only=True)); h=rows[0]; ub=[r for r in rows if r[4]=='BGD'][0]
U={int(h[i]):ub[i] for i in range(10,len(h)) if h[i] and str(h[i]).isdigit()}
P=lambda y: round(float(B[y]['TPopulation1July'])*1000)
def rank(y):
    pops=sorted(((float(v[y]['TPopulation1July']),k) for k,v in raw.items() if k!='World' and y in v and v[y]['LocTypeName']=='Country/Area' and v[y]['TPopulation1July']),reverse=True)
    return [k for _,k in pops].index('Bangladesh')+1
c=lambda n:f"{round(n):,}"
page=open('dist/country/bangladesh/population/index.html').read()
text=html.unescape(re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',re.sub(r'<script.*?</script>|<style.*?</style>','',page,flags=re.S))))
ld=json.dumps(json.loads(re.findall(r'<script type="application/ld\+json">(.*?)</script>',page,re.S)[0]))
y=2026
exp={
 'population 2026 (full)': c(P(y)),
 'population 2026 (millions)': f"{P(y)/1e6:.1f} million",
 'world rank 2026': f"{rank(y)}th",
 'share of world 2026': f"{P(y)/round(float(W[y]['TPopulation1July'])*1000)*100:.1f}%",
 'growth rate 2026': f"{float(B[y]['PopGrowthRate']):.1f}%",
 'yearly change 2026 (full)': c(float(B[y]['PopChange'])*1000),
 'yearly change 2026 (millions)': f"{float(B[y]['PopChange'])*1000/1e6:.1f} million",
 'per day 2026': c(float(B[y]['PopChange'])*1000/365),
 'density 2026': c(float(B[y]['PopDensity'])),
 'land area': c(P(2023)/float(B[2023]['PopDensity']))+' km²',
 'median age 2026': f"{float(B[y]['MedianAgePop']):.1f}",
 'median age 1980': f"{float(B[1980]['MedianAgePop']):.1f}",
 'median age 2050': f"{float(B[2050]['MedianAgePop']):.1f}",
 'fertility 2026': f"{float(B[y]['TFR']):.2f}",
 'fertility 1970': f"{float(B[1970]['TFR']):.2f}",
 'fertility 2000': f"{float(B[2000]['TFR']):.2f}",
 'fertility 2050': f"{float(B[2050]['TFR']):.2f}",
 'urban 2026 (WUP)': f"{U[y]:.1f}%",
 'urban 1960 (WUP)': f"{U[1960]:.1f}%",
 'urban 2050 (WUP)': f"{U[2050]:.1f}%",
 'urban people 2026': f"{P(y)*U[y]/100/1e6:.1f} million",
 'first urban-majority year': str(next(k for k in sorted(U) if U[k]>50)),
 'population 1960': f"{P(1960)/1e6:.1f} million",
 'grew times': f"{P(y)/P(1960):.1f} times",
 'density 1960': c(float(B[1960]['PopDensity'])),
 'population 2050': f"{P(2050)/1e6:.1f} million",
 'density 2050': c(float(B[2050]['PopDensity'])),
 'rank 2050': f"{rank(2050)}th",
 'growth 2050': f"{float(B[2050]['PopGrowthRate']):.1f}%",
 'net migrants 2026 (thousand)': f"{round(-float(B[y]['NetMigrations'])):,} thousand",
 'emigration peak year': str(min((float(B[k]['NetMigrations']),k) for k in range(1950,2024))[1]),
 'emigration peak (millions)': f"{-min(float(B[k]['NetMigrations']) for k in range(1950,2024))*1000/1e6:.1f} million",
 'negative every year since': str(next(s for s in range(1950,2024) if all(float(B[k]['NetMigrations'])<0 for k in range(s,2024)))),
 'Dhaka census (BBS)': '10,295,786',
}
for yr in (1960,1970,1980,1990,2000,2010,2020,2026,2030,2040,2050):
    exp[f'table pop {yr}']=c(P(yr)); exp[f'table rank {yr}']=None
bad=0
for k,v in exp.items():
    if v is None: continue
    ok=v in text
    if not ok: bad+=1
    print(('OK  ' if ok else 'MISS'), k, '=', v)
# JSON-LD numbers (FAQ answers, description) must equal page numbers
for k in ('population 2026 (millions)','density 2026','growth rate 2026','yearly change 2026 (millions)','population 2050','median age 2026'):
    v=exp[k]; ok=v in ld; bad+= (not ok); print(('OK  ' if ok else 'MISS'),'JSON-LD has',k,'=',v)
# CSV
csvt=open('dist/data/bangladesh-population.csv').read()
for yr in (1960,2026,2050):
    line=[l for l in csvt.splitlines() if l.startswith(f'{yr},')][0].split(',')
    good = int(line[1])==P(yr) and line[2]==str(round(float(B[yr]['PopDensity']))) and float(line[3])==round(float(B[yr]['TFR']),2) and float(line[5])==round(U[yr],1) and int(line[6])==round(float(B[yr]['NetMigrations'])*1000) and int(line[7])==rank(yr)
    bad+= (not good); print('OK  ' if good else 'MISS','CSV row',yr)
# Home page
home=html.unescape(open('dist/index.html').read())
wp=round(float(W[2026]['TPopulation1July'])*1000); wc=round(float(W[2026]['PopChange'])*1000)
for lab,v in [('home world anchor',f'data-anchor="{wp}"'),('home world rate',f'data-rate="{wc}"'),('home date','data-date="2026-07-01"'),('home 8.3 billion',f"{wp/1e9:.1f} billion"),('home change',f"{wc/1e6:.1f} million"),('home BD',f"{P(2026)/1e6:.1f} million")]:
    ok=v in home; bad+=(not ok); print(('OK  ' if ok else 'MISS'),lab,'=',v)
bd_live=f'data-anchor="{P(2026)}"' in page and f'data-rate="{round(float(B[2026]["PopChange"])*1000)}"' in page
bad+=(not bd_live); print('OK  ' if bd_live else 'MISS','BD live counter anchor/rate')
print('\nRESULT:', 'ALL MATCH' if not bad else f'{bad} mismatches')
