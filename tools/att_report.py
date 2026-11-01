import sys,datetime as D,collections,html; sys.path.insert(0,__import__('os').path.dirname(__file__))
from parse_frp import cells
recs=[];cur={}
import argparse
ap=argparse.ArgumentParser();ap.add_argument('out');ap.add_argument('files',nargs='+');ap.add_argument('--exclude',default='');ap.add_argument('--only',default='')
A=ap.parse_args()
allc=[c for f in A.files for c in cells(f)]
for x,y,t in allc:
    if x==36: cur={'id':t}
    elif x==122: cur['name']=t
    elif __import__('re').match(r'\d\d/\d\d/\d{4} \d\d:\d\d$',t): cur['dt']=t; recs.append(cur)
recs=[r for r in recs if r.get('dt','')[:2].isdigit() and r['id'] not in A.exclude.split(',') and (not A.only or r['id'] in A.only.split(','))]
names=collections.OrderedDict(); P=collections.defaultdict(lambda: collections.defaultdict(list))
for r in sorted(recs,key=lambda r:(int(r['id']),D.datetime.strptime(r['dt'],'%d/%m/%Y %H:%M'))):
    dt=D.datetime.strptime(r['dt'],'%d/%m/%Y %H:%M'); names[r['id']]=r['name']; P[r['id']][dt.day].append(dt.time())
import os
FD=os.path.join(os.path.dirname(os.path.abspath(__file__)),'fonts')
AR={'Sat':'السبت','Sun':'الأحد','Mon':'الاثنين','Tue':'الثلاثاء','Wed':'الأربعاء','Thu':'الخميس','Fri':'الجمعة'}
IN,OUT,CUT=D.time(7,0),D.time(14,30),D.time(11,0)
mins=lambda a,b:(a.hour*60+a.minute)-(b.hour*60+b.minute)
fmt=lambda m:f'{m//60}:{m%60:02d}'
summ=[];blocks=[]
for eid,nm in names.items():
    S=dict(work=0,full=0,miss_out=0,miss_in=0,absent=0,late_n=0,late_m=0,early_n=0,early_m=0)
    rows=[]
    for start in (1,11,21):
        hdr=[];cel=[]
        for d in range(start,start+10):
            day=D.date(2026,10,d); wd=day.strftime('%a'); hdr.append(f'<th>{d:02d}<br><small>{AR[wd]}</small></th>')
            ps=P[eid].get(d,[])
            i=next((p for p in ps if p<CUT),None); o=next((p for p in ps if p>=CUT),None)
            if wd=='Fri' and not ps: cel.append('<td class="fri">جمعة</td>'); continue
            S['work']+=1
            if not ps: S['absent']+=1; cel.append('<td class="abs">غياب</td>'); continue
            parts=[];cls=''
            h12=lambda t: f'{(t.hour-1)%12+1}:{t.minute:02d}'
            for k,(p,st,nk,lk,mk) in enumerate(((i,IN,'miss_in','late_n','late_m'),(o,OUT,'miss_out','early_n','early_m'))):
                if p:
                    l=mins(p,st)
                    if l>0: S[lk]+=1;S[mk]+=l; parts.append(f'<span class="late">{h12(p)}</span><small class="r"> +{l}د</small>')
                    else: parts.append(h12(p))
                else: S[nk]+=1; parts.append('<span class="miss">لم يبصم</span>'); cls='inc'
            if i and o: S['full']+=1
            cel.append(f'<td class="{cls}">{parts[0]}<br>{parts[1]}</td>')
        rows.append('<tr class="h">'+''.join(hdr)+'</tr><tr class="c">'+''.join(cel)+'</tr>')
    att=S['work']-S['absent']
    summ.append((eid,nm,S,att))
    blocks.append(f'''<div class="emp"><div class="eh"><span>رقم البصمة: <b>{eid}</b></span><span class="nm">{html.escape(nm)}</span>
<span>حضر <b>{att}</b> من {S['work']} يوم · غياب <b>{S['absent']}</b> · فترات بدون بصمة <b>{S['miss_in']+S['miss_out']}</b> · تأخير الفترة الأولى <b>{S['late_n']}</b> مرة ({fmt(S['late_m'])} ساعة) · تأخير الفترة الثانية <b>{S['early_n']}</b> مرة ({fmt(S['early_m'])} ساعة)</span></div>
<table class="g">{''.join(rows)}</table></div>''')
srows=''.join(f"<tr><td>{e}</td><td>{html.escape(n)}</td><td>{S['work']}</td><td>{a}</td><td class='{'bad' if S['absent'] else ''}'>{S['absent']}</td><td>{S['full']}</td><td class='{'bad' if S['miss_out'] else ''}'>{S['miss_out']}</td><td>{S['miss_in']}</td><td>{S['late_n']}</td><td>{fmt(S['late_m'])}</td><td>{S['early_n']}</td><td>{fmt(S['early_m'])}</td></tr>" for e,n,S,a in summ)
open(A.out,'w').write(f'''<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>
@font-face{{font-family:Naskh;font-weight:400;src:url("file://{FD}/noto-naskh-arabic-arabic-400-normal.woff2")}}
@font-face{{font-family:Naskh;font-weight:700;src:url("file://{FD}/noto-naskh-arabic-arabic-700-normal.woff2")}}
@page{{size:A4 landscape;margin:9mm}}body{{font-family:Naskh,"DejaVu Sans",sans-serif;font-size:10.5px;color:#1d2433;line-height:1.15}}
h1{{font-size:17px;margin:0;color:#0f3d5e;text-align:center}}.sub{{text-align:center;color:#556;margin:2px 0 8px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #9fb0c0;text-align:center;padding:3px 2px}}
.sum th{{background:#0f3d5e;color:#fff;font-size:9.5px}}.sum td{{font-size:11px;padding:2px}}.bad{{color:#b02a2a;font-weight:bold}}
.emp{{margin-top:9px;page-break-inside:avoid}}.eh{{display:flex;justify-content:space-between;background:#0f3d5e;color:#fff;padding:4px 8px;font-size:10px}}
.nm{{font-size:12px;font-weight:bold}}.g tr.h th{{background:#dde7f0;font-size:9.5px;width:10%;padding:1px}}.g tr.c td{{height:26px;font-size:11px;line-height:1.15;padding:1px}}
.fri{{background:#eceff2;color:#889}}.abs{{background:#f8d7d7;color:#b02a2a;font-weight:bold}}.inc{{background:#fff3d6}}
.late{{color:#b02a2a;font-weight:bold}}.miss{{color:#c27a00;font-weight:bold;font-size:9px}}.r{{color:#b02a2a;font-size:8px}}
.leg{{margin:6px 0;font-size:9.5px}}.leg span{{display:inline-block;padding:1px 7px;margin-left:8px;border:1px solid #bbb}}
</style></head><body>
<h1>جدول حضور وانصراف السواقين</h1><div class="sub">الفترة 2026-10-01 إلى 2026-10-30 · الفترة الأولى 7:00 · الفترة الثانية 2:30 · الجمعة إجازة</div>
<table class="sum"><tr><th>رقم البصمة</th><th>الاسم</th><th>أيام العمل</th><th>أيام الحضور</th><th>غياب</th><th>أيام كاملة (الفترتين)</th><th>لم يبصم الفترة الثانية</th><th>لم يبصم الفترة الأولى</th><th>تأخير الفترة الأولى (مرات)</th><th>مجموع التأخير ف1</th><th>تأخير الفترة الثانية (مرات)</th><th>مجموع التأخير ف2</th></tr>{srows}</table>
<div class="leg"><span style="background:#f8d7d7">غياب</span><span style="background:#fff3d6">فترة بدون بصمة</span><span style="color:#b02a2a">أحمر = تأخير بعد 7:00 أو بعد 2:30 (بالدقائق)</span><span style="background:#eceff2">جمعة</span></div>
<div style="font-size:9px;color:#556">طريقة القراءة: في كل خانة السطر الأول بصمة الفترة الأولى (7:00) والسطر الثاني بصمة الفترة الثانية (2:30). البصمة المكررة في نفس الفترة حُسبت مرة وحدة (الأولى فقط).</div>
{''.join(blocks)}
<div style="margin-top:8px;font-size:8.5px;color:#889">ملاحظة: الأسماء مختصرة كما هي في جهاز البصمة.</div></body></html>''')
for e,n,S,a in summ: print(e,n,S,a)
