#!/usr/bin/env python3
"""مطابقة تلقائية بين كشفين (Excel/CSV).

الاستخدام:
  python3 tools/reconcile.py A.xlsx B.xlsx --out result.xlsx [خيارات]

يطابق بالمبلغ أولًا (+ المرجع إن وُجد)، ثم بأقرب تاريخ ضمن --days.
الناتج: Excel فيه أوراق: ملخص، متطابق، في_A_فقط، في_B_فقط، تنبيهات.
"""
import argparse
import sys

import pandas as pd

AMOUNT_HINTS = ["amount", "المبلغ", "مبلغ", "القيمة"]
DEBIT_HINTS = ["debit", "مدين", "dr"]
CREDIT_HINTS = ["credit", "دائن", "cr"]
DATE_HINTS = ["date", "التاريخ", "تاريخ"]
REF_HINTS = ["ref", "reference", "المرجع", "مرجع", "رقم", "doc", "سند"]


def read(path):
    if path.lower().endswith((".xlsx", ".xls")):
        return pd.read_excel(path)
    return pd.read_csv(path)


def find(cols, hints):
    for c in cols:
        lc = str(c).strip().lower()
        if any(h in lc for h in hints):
            return c
    return None


def to_num(s):
    return pd.to_numeric(
        s.astype(str).str.replace(",", "").str.replace("(", "-").str.replace(")", "").str.strip(),
        errors="coerce",
    ).fillna(0)


def normalize(df, amount, date, ref, flip, label):
    cols = list(df.columns)
    amount = amount or find(cols, AMOUNT_HINTS)
    if amount:
        amt = to_num(df[amount])
    else:
        d, c = find(cols, DEBIT_HINTS), find(cols, CREDIT_HINTS)
        if not (d and c):
            sys.exit(f"[{label}] لم أجد عمود مبلغ ولا مدين/دائن. حدده بـ --{label.lower()}-amount. الأعمدة: {cols}")
        amt = to_num(df[d]) - to_num(df[c])
    date = date or find(cols, DATE_HINTS)
    ref = ref or find(cols, REF_HINTS)
    out = pd.DataFrame({
        "row": df.index + 2,
        "amount": (-amt if flip else amt).round(2),
        "date": pd.to_datetime(df[date], errors="coerce", dayfirst=True) if date else pd.NaT,
        "ref": df[ref].astype(str).str.strip() if ref else "",
    })
    out = pd.concat([out, df.add_prefix("orig_")], axis=1)
    return out[out["amount"] != 0].reset_index(drop=True)


def match(a, b, days):
    used_b, pairs = set(), []
    for pass_ref in (True, False):
        for i, ra in a.iterrows():
            if i in {p[0] for p in pairs}:
                continue
            cand = b[(b["amount"] == ra["amount"]) & (~b.index.isin(used_b))]
            if pass_ref:
                if not ra["ref"] or ra["ref"] == "nan":
                    continue
                cand = cand[cand["ref"] == ra["ref"]]
            if cand.empty:
                continue
            if pd.notna(ra["date"]) and cand["date"].notna().any():
                gap = (cand["date"] - ra["date"]).abs().dt.days
                cand = cand[gap <= days]
                if cand.empty:
                    continue
                j = gap.loc[cand.index].idxmin()
            else:
                j = cand.index[0]
            used_b.add(j)
            pairs.append((i, j))
    return pairs


def alerts(only_a, only_b, diff):
    notes = []
    if diff and round(abs(diff) * 100) % 900 == 0:
        notes.append(f"الفرق ({diff:,.2f}) يقبل القسمة على 9 → احتمال أرقام مقلوبة أو خطأ خانة.")
    for side, df in (("A", only_a), ("B", only_b)):
        dup = df[df.duplicated(["amount", "date"], keep=False)]
        for _, r in dup.iterrows():
            notes.append(f"تكرار محتمل في {side}: سطر {r['row']} مبلغ {r['amount']:,.2f}")
        for _, r in df.iterrows():
            if diff and abs(abs(r["amount"]) * 2 - abs(diff)) < 0.01:
                notes.append(f"سطر {r['row']} في {side} ({r['amount']:,.2f}) = نصف الفرق → احتمال قيد بعكس الاتجاه.")
            if diff and abs(abs(r["amount"]) - abs(diff)) < 0.01:
                notes.append(f"سطر {r['row']} في {side} ({r['amount']:,.2f}) = الفرق بالضبط.")
    for _, ra in only_a.iterrows():
        for _, rb in only_b.iterrows():
            if abs(ra["amount"] + rb["amount"]) < 0.01:
                notes.append(f"A سطر {ra['row']} و B سطر {rb['row']} نفس المبلغ بإشارة معكوسة → جرّب --flip-b أو تحقق من الاتجاه.")
            elif ra["amount"] and rb["amount"] and abs(ra["amount"] - rb["amount"]) % 9 == 0 and \
                    sorted(str(abs(int(ra["amount"])))) == sorted(str(abs(int(rb["amount"])))):
                notes.append(f"A سطر {ra['row']} ({ra['amount']:,.2f}) و B سطر {rb['row']} ({rb['amount']:,.2f}) → أرقام مقلوبة.")
    return notes


def main():
    p = argparse.ArgumentParser(description="مطابقة كشفين")
    p.add_argument("a"); p.add_argument("b")
    p.add_argument("--out", default="مطابقة.xlsx")
    for s in ("a", "b"):
        for f in ("amount", "date", "ref"):
            p.add_argument(f"--{s}-{f}")
    p.add_argument("--flip-b", action="store_true", help="اعكس إشارة الكشف B")
    p.add_argument("--days", type=int, default=3)
    x = p.parse_args()

    a = normalize(read(x.a), x.a_amount, x.a_date, x.a_ref, False, "A")
    b = normalize(read(x.b), x.b_amount, x.b_date, x.b_ref, x.flip_b, "B")
    pairs = match(a, b, x.days)
    ia, ib = [p[0] for p in pairs], [p[1] for p in pairs]
    matched = pd.concat([a.loc[ia].reset_index(drop=True).add_prefix("A_"),
                         b.loc[ib].reset_index(drop=True).add_prefix("B_")], axis=1)
    only_a, only_b = a.drop(index=ia), b.drop(index=ib)
    ta, tb = a["amount"].sum(), b["amount"].sum()
    diff = round(ta - tb, 2)
    notes = alerts(only_a, only_b, diff)

    summary = pd.DataFrame({"البند": ["مجموع A", "مجموع B", "الفرق (A-B)", "عدد المتطابق",
                                      "في A فقط (عدد/مبلغ)", "في B فقط (عدد/مبلغ)"],
                            "القيمة": [round(ta, 2), round(tb, 2), diff, len(pairs),
                                       f"{len(only_a)} / {only_a['amount'].sum():,.2f}",
                                       f"{len(only_b)} / {only_b['amount'].sum():,.2f}"]})
    with pd.ExcelWriter(x.out, engine="openpyxl") as w:
        summary.to_excel(w, sheet_name="ملخص", index=False)
        matched.to_excel(w, sheet_name="متطابق", index=False)
        only_a.to_excel(w, sheet_name="في_A_فقط", index=False)
        only_b.to_excel(w, sheet_name="في_B_فقط", index=False)
        pd.DataFrame({"تنبيه": notes or ["لا يوجد"]}).to_excel(w, sheet_name="تنبيهات", index=False)
        for ws in w.book.worksheets:
            ws.sheet_view.rightToLeft = True

    print(summary.to_string(index=False))
    print("\nتنبيهات:"); print("\n".join(f"- {n}" for n in notes) or "- لا يوجد")
    print(f"\nالملف: {x.out}")


if __name__ == "__main__":
    main()
