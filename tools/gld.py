# date-anchored parser: debit/credit by right-edge position, balance optional
import pdfplumber,re,json,sys
src,out=sys.argv[1],sys.argv[2]; dx=(float(sys.argv[3]),float(sys.argv[4])); cr_r=float(sys.argv[5]); dr_r=float(sys.argv[6]); descx=float(sys.argv[7])
NUM=re.compile(r'^[\d,]+\.\d\d$'); DT=re.compile(r'^20\d\d/\d\d/\d\d$')
def rv(w): return w if re.search(r'\d',w) and not re.search(r'[؀-ۿ]',w) else w[::-1]
rows=[]
for pi,p in enumerate(pdfplumber.open(src).pages):
    ws=p.extract_words()
    for d in [w for w in ws if DT.match(w['text']) and dx[0]<w['x0']<dx[1]]:
        line=[w for w in ws if abs(w['top']-d['top'])<3]
        nums=[w for w in line if NUM.match(w['text']) and w['x1']<d['x0']]
        def near(r): 
            c=[w for w in nums if abs(w['x1']-r)<6]; return float(c[0]['text'].replace(',','')) if c else None
        dr,cr=near(dr_r),near(cr_r)
        bal=[w for w in line if NUM.match(w['text']) and w['x1']<descx+45 and w['x0']>descx-40]
        desc=sorted([w for w in ws if w['x1']<descx and abs(w['top']-d['top'])<=12 and not NUM.match(w['text'])],key=lambda w:(round(w['top']/4),-w['x0']))
        right=[w['text'] for w in line if w['x0']>d['x1']]
        rows.append(dict(pg=pi+1,top=round(d['top'],1),date=d['text'],dr=dr,cr=cr,right=right,desc=' '.join(rv(w['text']) for w in desc),bal=[b['text'] for b in bal]))
rows.sort(key=lambda r:(r['pg'],r['top']))
json.dump(rows,open(out,'w'),ensure_ascii=False)
print(len(rows),'rows; missing dr/cr:',sum(1 for r in rows if r['dr'] is None or r['cr'] is None))
print('totals dr',round(sum(r['dr'] or 0 for r in rows),2),'cr',round(sum(r['cr'] or 0 for r in rows),2))
