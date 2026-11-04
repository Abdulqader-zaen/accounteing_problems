# GL parser (compact layout): anchor = date in x 420-475; debit right-edge ~408, credit ~369, balance 268-304 + side word
import pdfplumber,re,json,sys
src,out=sys.argv[1],sys.argv[2]
NUM=re.compile(r'^-?[\d,]+\.\d\d$'); DT=re.compile(r'^20\d\d/\d\d/\d\d$')
def rv(w): return w if re.search(r'\d',w) and not re.search(r'[؀-ۿ]',w) else w[::-1]
rows=[]
for pi,p in enumerate(pdfplumber.open(src).pages):
    ws=p.extract_words()
    for d in [w for w in ws if DT.match(w['text']) and 420<w['x0']<475]:
        t=d['top']; line=[w for w in ws if abs(w['top']-t)<2.5]
        def near(r):
            c=[w for w in line if NUM.match(w['text']) and abs(w['x1']-r)<5]; return float(c[0]['text'].replace(',','')) if c else None
        dr,cr=near(408.5),near(369.5)
        b=sorted([w for w in ws if NUM.match(w['text']) and 255<w['x0']<305 and abs(w['top']-t)<=6.5],key=lambda w:abs(w['top']-t))
        side=[w['text'] for w in sorted(ws,key=lambda w:abs(w['top']-t)) if w['text'] in('نيدم','نئاد') and 300<w['x0']<330 and abs(w['top']-t)<=6.5]
        bal=None
        if b: bal=float(b[0]['text'].replace(',',''))*(1 if side and side[0]=='نيدم' else -1)
        doc=[w['text'] for w in line if re.match(r'^\d+$',w['text']) and 470<w['x0']<500]
        seq=[w['text'] for w in line if re.match(r'^\d+$',w['text']) and w['x0']>548 and w['x1']>565]
        win=[w for w in ws if abs(w['top']-t)<=8.5 and w not in line or (w in line and w['x1']<266)]
        desc=sorted([w for w in win if w['x1']<266 and not NUM.match(w['text'])],key=lambda w:(round(w['top']),-w['x0']))
        typ=sorted([w for w in ws if abs(w['top']-t)<=8.5 and 505<w['x0']<555],key=lambda w:(round(w['top']),-w['x0']))
        rows.append(dict(pg=pi+1,top=round(t,1),date=d['text'].replace('/','-'),doc=doc[0] if doc else '',seq=int(seq[0]) if seq else None,dr=dr,cr=cr,bal=bal,
            typ=' '.join(rv(w['text']) for w in typ),desc=' '.join(rv(w['text']) for w in desc)))
    seen={r['seq'] for r in rows if r['pg']==pi+1}
    for q in [w for w in ws if re.match(r'^\d+$',w['text']) and w['x0']>548 and w['x1']>565 and w['top']>85]:
        if int(q['text']) in seen or int(q['text'])==1: continue
        t=q['top']
        b=sorted([w for w in ws if NUM.match(w['text']) and 255<w['x0']<305 and abs(w['top']-t)<=6.5],key=lambda w:abs(w['top']-t))
        side=[w['text'] for w in sorted(ws,key=lambda w:abs(w['top']-t)) if w['text'] in('نيدم','نئاد') and 300<w['x0']<330 and abs(w['top']-t)<=6.5]
        bal=float(b[0]['text'].replace(',',''))*(1 if side and side[0]=='نيدم' else -1)
        desc=sorted([w for w in ws if abs(w['top']-t)<=8.5 and w['x1']<266 and not NUM.match(w['text'])],key=lambda w:(round(w['top']),-w['x0']))
        typ=sorted([w for w in ws if abs(w['top']-t)<=8.5 and 505<w['x0']<555 and abs(w['top']-t)>2],key=lambda w:(round(w['top']),-w['x0']))
        rows.append(dict(pg=pi+1,top=round(t,1),date=None,doc='?',seq=int(q['text']),dr=None,cr=None,bal=bal,recovered=1,
            typ=' '.join(rv(w['text']) for w in typ),desc=' '.join(rv(w['text']) for w in desc)))
rows.sort(key=lambda r:(r['pg'],r['top']))
rows=[r for r in rows if not (r['seq'] is None and r['dr'] is None)] if False else rows
prev=None
for k,r in enumerate(rows):
    if r.get('recovered'):
        a=round(r['bal']-prev,2); r['dr'],r['cr']=(a,0.0) if a>=0 else (0.0,-a)
        r['date']=rows[k+1]['date'] if k+1<len(rows) else rows[k-1]['date']
    if r['dr'] is None and r['seq'] is None: r['dr'],r['cr']=0.0,0.0; r['opening']=1
    elif r['dr'] is None: r['dr']=round(r['bal']-prev,2); r['fixed']=1
    prev=r['bal']
for r in rows:
    if r['dr'] is None or r['cr'] is None: print('MISSING',r)
json.dump(rows,open(out,'w'),ensure_ascii=False)
print(len(rows),'rows; missing dr/cr',sum(1 for r in rows if r['dr'] is None or r['cr'] is None),'missing bal',sum(1 for r in rows if r['bal'] is None))
s=[r['seq'] for r in rows if r['seq']]; print('seq',min(s),max(s),'missing',sorted(set(range(min(s),max(s)+1))-set(s))[:30])
prev=None;br=[]
for r in rows:
    if prev is not None and r['bal'] is not None and r['dr'] is not None and abs(prev+r['dr']-r['cr']-r['bal'])>0.005: br.append((r['seq'],prev,r['dr'],r['cr'],r['bal']))
    if r['bal'] is not None: prev=r['bal']
print('chain breaks',len(br),br[:8])
print('dr',round(sum(r['dr'] or 0 for r in rows),2),'cr',round(sum(r['cr'] or 0 for r in rows),2))
