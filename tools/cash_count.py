#!/usr/bin/env python3
"""حساب عجز/زيادة الصندوق اليومي.

الاستخدام:
  python3 tools/cash_count.py templates/صندوق_يومي.csv
الملف بعمودين: البند,القيمة (انظر القالب). أسطر الجرد تبدأ بـ "فئة " مثل: فئة 500,3 (عدد الأوراق).
"""
import csv
import sys

PLUS = ["رصيد أول المدة", "مبيعات نقدية", "مقبوضات أخرى"]
MINUS = ["مصروفات نثرية", "مرتجعات نقدية", "سلف", "توريد للبنك"]


def main(path):
    vals, counted, rows = {}, 0.0, []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.reader(f):
            if len(r) < 2 or not r[1].strip() or r[0].strip() == "البند":
                continue
            k, v = r[0].strip(), float(r[1].replace(",", ""))
            if k.startswith("فئة "):
                denom = float(k.split()[1])
                counted += denom * v
                rows.append((f"  {k} × {v:g}", denom * v))
            elif k == "جرد فعلي":
                counted += v
            else:
                vals[k] = vals.get(k, 0) + v
    expected = sum(vals.get(k, 0) for k in PLUS) - sum(vals.get(k, 0) for k in MINUS)
    print("الرصيد المتوقع:")
    for k in PLUS:
        print(f"  + {k}: {vals.get(k, 0):,.2f}")
    for k in MINUS:
        print(f"  - {k}: {vals.get(k, 0):,.2f}")
    print(f"  = {expected:,.2f}\n\nالجرد الفعلي:")
    for k, v in rows:
        print(f"{k} = {v:,.2f}")
    print(f"  = {counted:,.2f}\n")
    d = round(counted - expected, 2)
    kind = "عجز" if d < 0 else "زيادة" if d > 0 else "مطابق"
    print(f"النتيجة: {kind} {abs(d):,.2f}")
    if d and round(abs(d) * 100) % 900 == 0:
        print("تنبيه: الفرق يقبل القسمة على 9 → احتمال أرقام مقلوبة.")
    if "مبيعات شبكة" in vals:
        print(f"تذكير: قارن مبيعات الشبكة ({vals['مبيعات شبكة']:,.2f}) بتقرير جهاز POS — أي فرق هناك غالبًا هو نفس فرق الصندوق.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "templates/صندوق_يومي.csv")
