import pdfplumber,re,json,sys
src,out,bx0,bx1,nx0,nx1,dx1,doc0,doc1=sys.argv[1],sys.argv[2],*map(float,sys.argv[3:10])
NUM=re.compile(r'^-?[\d,]+\.\d\d$')
def rv(w): return w if re.search(r'\d',w) and not re.search(r'[؀-ۿ]',w) else w[::-1]
rows=[]
for pi,p in enumerate(pdfplumber.open(src).pages):
    ws=p.extract_words()
    for b in [w for w in ws if NUM.match(w['text']) and bx0<w['x0']<bx1]:
        side=[w for w in ws if abs(w['top']-b['top'])<3 and w['text'] in('نيدم','نئاد') and 0<w['x0']-b['x1']<12]
        if not side: continue
        line=[w for w in ws if abs(w['top']-b['top'])<3]
        date=[w['text'] for w in line if re.match(r'^20\d\d/\d\d/\d\d$',w['text'])]
        nums=[w['text'] for w in line if NUM.match(w['text']) and nx0<w['x0']<nx1]
        seq=[w['text'] for w in line if re.match(r'^\d+$',w['text']) and w['x0']>540]
        doc=[w['text'] for w in line if re.match(r'^\d+$',w['text']) and doc0<w['x0']<doc1]
        desc=sorted([w for w in ws if w['x1']<dx1 and abs(w['top']-b['top'])<=12],key=lambda w:(round(w['top']/4),-w['x0']))
        rows.append(dict(pg=pi+1,top=b['top'],bal=(1 if side[0]['text']=='نيدم' else -1)*float(b['text'].replace(',','')),date=date[0] if date else '',doc=doc[0] if doc else '',seq=seq[0] if seq else '',nums=nums,desc=' '.join(rv(w['text']) for w in desc)))
rows.sort(key=lambda r:(r['pg'],r['top'])); prev=None; last=''
for r in rows:
    r['amt']=round(r['bal']-(prev if prev is not None else 0),2); prev=r['bal']
    if not r['date']: r['date']=last; r['nodate']=1
    last=r['date']
    n=[float(x.replace(',','')) for x in r['nums']]
    r['chk']=(abs(abs(r['amt'])-max(n))<0.01) if n else None
json.dump(rows,open(out,'w'),ensure_ascii=False)
bad=[(r['pg'],r['seq'],r['amt'],r['nums']) for r in rows if r['chk'] is False]
print(len(rows),'rows; amount/balance mismatches:',len(bad),bad[:10])
seqs=[int(r['seq']) for r in rows if r['seq']]; 
print('seq range',min(seqs),max(seqs),'missing seq:',sorted(set(range(min(seqs),max(seqs)+1))-set(seqs))[:40])
