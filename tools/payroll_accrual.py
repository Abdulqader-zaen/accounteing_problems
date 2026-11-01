#!/usr/bin/env python3
"""بناء قيد استحقاق الرواتب (Amnx) لشهر جديد من قيد الشهر السابق + كشف الرواتب.
python3 tools/payroll_accrual.py قيد_سابق.Amnx كشف.xlsx "اسم الورقة" 10 2026 out.Amnx
"""
import re, sys, copy, openpyxl
prev, xlsx, sheet, mon, yr, out = sys.argv[1:7]; mon=int(mon)
MM=f'{mon:02d}'
src=open(prev, encoding='utf-8-sig').read()
head=src[:src.index('</xs:schema>')+len('</xs:schema>')]
mst=re.search(r'<DOC_MST_TABLE>.*?</DOC_MST_TABLE>', src, re.S).group(0)
dets=re.findall(r'<DOC_DET_TABLE>.*?</DOC_DET_TABLE>', src, re.S)
ws=openpyxl.load_workbook(xlsx, data_only=True)[sheet]
def norm(s): return re.sub(r'[\sـ]+',' ',str(s or '')).replace('أ','ا').replace('إ','ا').replace('ة','ه').replace('ى','ي').strip()
rows=[]
for r in range(1, ws.max_row+1):
    v=lambda c: ws.cell(r,c).value
    if isinstance(v(5),(int,float)) and isinstance(v(12),(int,float)) and v(12)>0 and v(2) and norm(v(2))!='الاجمالي':
        rows.append(dict(r=r,name=str(v(2)).strip(),E=v(5) or 0,F=v(6) or 0,H=v(8) or 0,I=v(9) or 0,J=v(10) or 0,K=v(11) or 0,L=v(12),N=v(14) or 0,G=v(7)))
# match sheet rows to accounts: name similarity (manual map for known differences)
ALIAS={'125011':'صالح عبد الرب','125019':'عليه احمد','125040':'قاصد','125048':'زهرا','125041':'هداشه','125033':'خالد معاضه|خالد معوضه','125051':'شبير','125028':'هايل','125020':'مختار'}
def acct(d): return re.search(r'<AC_NO>(\d+)</AC_NO>',d).group(1), re.search(r'<AC_ARNAME>(.*?)</AC_ARNAME>',d).group(1)
used=set(); emp_lines=[]; other=[]
for d in dets:
    no,nm=acct(d)
    if not no.startswith('125'): other.append(d); continue
    key=norm(nm.split('_',1)[1]).replace('راتب ','').replace('الموظفه ','')
    pats=ALIAS.get(no,key).split('|')
    cand=[x for x in rows if x['r'] not in used and any(norm(p) in norm(x['name']) or norm(x['name']) in norm(p) for p in pats)]
    if len(cand)>1:
        ex=[c for c in cand if any(norm(c['name'])==norm(p) for p in pats)]
        if len(ex)==1: cand=ex
    if len(cand)!=1: sys.exit(f'مطابقة غير واضحة للحساب {no} {nm}: {[c["name"] for c in cand]}')
    used.add(cand[0]['r']); emp_lines.append((d,cand[0]))
new=[x for x in rows if x['r'] not in used]
def note(x):
    t=f'استحقاق راتب عن شهر{MM}-{yr}'
    if x['J']: t+=f" + اضافي {x['J']:g}"
    if x['F'] and 'حراج' in str(x['G'] or ''): t+=f" + {x['F']:g} الحراج"
    elif x['F'] and x['I']: t+=f" + {x['F']:g} بدل مواصلات"
    if x['H']: t+=f" + {x['H']:g} بدل سكن"
    if x['I']: t+=f" + {x['I']:g} بدل اتصال وفطور"
    if x['K']: t+=f" - خصم {x['K']:g}"
    if x['N']: t+=f" - خصمت {x['N']:g} قسط سلفة"
    return t
date=f'{yr}-{MM}-{ {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}[mon] :02d}T17:00:00+03:00'
def setf(d,tag,val): return re.sub(rf'<{tag}>.*?</{tag}>|<{tag} />', f'<{tag}>{val}</{tag}>', d, count=1, flags=re.S)
total=sum(x['L'] for x in rows)
outd=[]
for d in other[:1]:  # salaries expense line first
    d=setf(d,'DOC_D_FORIGNVALUE',f'{total:g}'); d=setf(d,'DOC_D_NOTA_1',f'استحقاق رواتب الموظفين عن شهر {yr}-{mon}'); outd.append(d)
for d,x in emp_lines:
    d=setf(d,'DOC_D_FORIGNVALUE',f"{x['L']:g}"); d=setf(d,'DOC_D_NOTA_1',note(x)); outd.append(d)
for x in new:
    d=emp_lines[0][0]; d=setf(d,'AC_ID','0'); d=setf(d,'AC_NO',''); d=setf(d,'AC_ARNAME',f"{x['name']} (موظف جديد - اختر الحساب)")
    d=setf(d,'DOC_D_FORIGNVALUE',f"{x['L']:g}"); d=setf(d,'DOC_D_NOTA_1',note(x)); outd.append(d)
for d in other[1:]:
    n=re.search(r'<DOC_D_NOTA_1>(.*?)</DOC_D_NOTA_1>',d).group(1)
    n=re.sub(r'(\D)0?\d{1,2}-'+yr, lambda m: f'{m.group(1)}{MM}-{yr}', n); outd.append(setf(d,'DOC_D_NOTA_1',n))
outd=[setf(setf(d,'DOC_D_DATE',date),'DOC_D_ID',str(i)) for i,d in enumerate(outd)]
dr=sum(float(re.search(r'<DOC_D_FORIGNVALUE>(.*?)<',d).group(1)) for d in outd if '<DOC_D_STATE>1<' in d)
cr=sum(float(re.search(r'<DOC_D_FORIGNVALUE>(.*?)<',d).group(1)) for d in outd if '<DOC_D_STATE>2<' in d)
assert abs(dr-cr)<0.005, (dr,cr)
m=mst
for t,v in (('DOC_ID','0'),('DOC_ID_1','0'),('DOC_NO','0'),('DOC_DATE',date),('DOC_FORIGNVALUE',f'{dr:g}'),('DOC_NOTA_1',f'استحقاق رواتب الموظفين عن شهر {yr}-{mon}')): m=setf(m,t,v)
open(out,'w',encoding='utf-8').write(head+'\n  '+m+'\n  '+'\n  '.join(outd)+'\n</NewDataSet>')
print(f'سطور: {len(outd)} | مدين {dr:,.2f} = دائن {cr:,.2f} | موظفين جدد: {[x["name"] for x in new]}')
