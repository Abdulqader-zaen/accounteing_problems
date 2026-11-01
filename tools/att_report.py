import sys,datetime as D,collections,html; sys.path.insert(0,__import__('os').path.dirname(__file__))
from parse_frp import cells
recs=[];cur={}
for x,y,t in cells(sys.argv[1]):
    if x==36: cur={'id':t}
    elif x==122: cur['name']=t
    elif x==178: cur['dt']=t
    elif x==414: cur['exc']=t; recs.append(cur)
recs=[r for r in recs if r.get('dt','')[:2].isdigit()]
names=collections.OrderedDict(); P=collections.defaultdict(lambda: collections.defaultdict(list))
for r in sorted(recs,key=lambda r:(int(r['id']),D.datetime.strptime(r['dt'],'%d/%m/%Y %H:%M'))):
    dt=D.datetime.strptime(r['dt'],'%d/%m/%Y %H:%M'); names[r['id']]=r['name']; P[r['id']][dt.day].append(dt.time())
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
            if i:
                l=mins(i,IN)
                if l>0: S['late_n']+=1;S['late_m']+=l; parts.append(f'<span class="late">{i:%H:%M}</span><small class="r"> +{l}د</small>')
                else: parts.append(f'{i:%H:%M}')
            else: S['miss_in']+=1; parts.append('<span class="miss">بدون حضور</span>'); cls='inc'
            if o:
                e=mins(OUT,o)
                if e>0: S['early_n']+=1;S['early_m']+=e; parts.append(f'<span class="late">{o:%H:%M}</span><small class="r"> -{e}د</small>')
                else: parts.append(f'{o:%H:%M}')
            else: S['miss_out']+=1; parts.append('<span class="miss">بدون انصراف</span>'); cls='inc'
            if i and o: S['full']+=1
            cel.append(f'<td class="{cls}">{parts[0]}<br>{parts[1]}</td>')
        rows.append('<tr class="h">'+''.join(hdr)+'</tr><tr class="c">'+''.join(cel)+'</tr>')
    att=S['work']-S['absent']
    summ.append((eid,nm,S,att))
    blocks.append(f'''<div class="emp"><div class="eh"><span>رقم البصمة: <b>{eid}</b></span><span class="nm">{html.escape(nm)}</span>
<span>حضر <b>{att}</b> من {S['work']} يوم · غياب <b>{S['absent']}</b> · بصمة ناقصة <b>{S['miss_in']+S['miss_out']}</b> · تأخير <b>{S['late_n']}</b> مرة ({fmt(S['late_m'])} ساعة) · خروج مبكر <b>{S['early_n']}</b> مرة ({fmt(S['early_m'])} ساعة)</span></div>
<table class="g">{''.join(rows)}</table></div>''')
srows=''.join(f"<tr><td>{e}</td><td>{html.escape(n)}</td><td>{S['work']}</td><td>{a}</td><td class='{'bad' if S['absent'] else ''}'>{S['absent']}</td><td>{S['full']}</td><td class='{'bad' if S['miss_out'] else ''}'>{S['miss_out']}</td><td>{S['miss_in']}</td><td>{S['late_n']}</td><td>{fmt(S['late_m'])}</td><td>{S['early_n']}</td><td>{fmt(S['early_m'])}</td></tr>" for e,n,S,a in summ)
open(sys.argv[2],'w').write(f'''<!DOCTYPE html><html lang="ar" dir="rtl"><head><meta charset="utf-8"><style>
@page{{size:A4 landscape;margin:9mm}}body{{font-family:"DejaVu Sans",sans-serif;font-size:9.5px;color:#1d2433}}
h1{{font-size:17px;margin:0;color:#0f3d5e;text-align:center}}.sub{{text-align:center;color:#556;margin:2px 0 8px}}
table{{border-collapse:collapse;width:100%}}td,th{{border:1px solid #9fb0c0;text-align:center;padding:3px 2px}}
.sum th{{background:#0f3d5e;color:#fff;font-size:9.5px}}.sum td{{font-size:10.5px;padding:5px}}.bad{{color:#b02a2a;font-weight:bold}}
.emp{{margin-top:9px;page-break-inside:avoid}}.eh{{display:flex;justify-content:space-between;background:#0f3d5e;color:#fff;padding:4px 8px;font-size:10px}}
.nm{{font-size:12px;font-weight:bold}}.g tr.h th{{background:#dde7f0;font-size:9px;width:10%}}.g tr.c td{{height:30px;font-size:10px;line-height:1.35}}
.fri{{background:#eceff2;color:#889}}.abs{{background:#f8d7d7;color:#b02a2a;font-weight:bold}}.inc{{background:#fff3d6}}
.late{{color:#b02a2a;font-weight:bold}}.miss{{color:#c27a00;font-weight:bold;font-size:9px}}.r{{color:#b02a2a;font-size:8px}}
.leg{{margin:6px 0;font-size:9.5px}}.leg span{{display:inline-block;padding:1px 7px;margin-left:8px;border:1px solid #bbb}}
</style></head><body>
<h1>جدول حضور وانصراف السواقين</h1><div class="sub">الفترة 2026-10-01 إلى 2026-10-30 · الحضور 7:00 ص · الانصراف 2:30 م · الجمعة إجازة</div>
<table class="sum"><tr><th>رقم البصمة</th><th>الاسم</th><th>أيام العمل</th><th>أيام الحضور</th><th>غياب</th><th>أيام كاملة</th><th>بدون انصراف</th><th>بدون حضور</th><th>مرات التأخير</th><th>إجمالي التأخير</th><th>مرات الخروج المبكر</th><th>إجمالي الخروج المبكر</th></tr>{srows}</table>
<div class="leg"><span style="background:#f8d7d7">غياب</span><span style="background:#fff3d6">بصمة ناقصة</span><span style="color:#b02a2a">أحمر = تأخير بعد 7:00 أو خروج قبل 2:30 (بالدقائق)</span><span style="background:#eceff2">جمعة</span></div>
<div style="font-size:9px;color:#556">طريقة القراءة: في كل خانة السطر الأول وقت الحضور والثاني وقت الانصراف. البصمة المكررة في نفس الفترة حُسبت مرة وحدة (الأولى فقط).</div>
{''.join(blocks)}
<div style="margin-top:8px;font-size:8.5px;color:#889">ملاحظة: الأسماء مختصرة كما هي في جهاز البصمة.</div></body></html>''')
for e,n,S,a in summ: print(e,n,S,a)
