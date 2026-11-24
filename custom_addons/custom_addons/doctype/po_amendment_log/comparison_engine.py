"""Pure-python PO comparison logic (no frappe imports, so it is unit-testable).

Row dict keys: po_detail, item_code, item_name, description, uom, qty, rate, amount,
schedule_date, warehouse, material_request, material_request_item.

Rules follow the handoff spec (sections 7-9):
- never match on row position; identity = unique (MR, MR item, item code), then a unique item code;
- different item codes are never equivalent; repeated rows without unique lineage are Unresolved;
- N/A is explicit (qty/rate/amount_comparable flags), never an implied zero.
"""
import datetime
from collections import defaultdict


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def _d(v):
    if not v:
        return None
    if isinstance(v, datetime.datetime):
        return v.date()
    if isinstance(v, datetime.date):
        return v
    return datetime.date.fromisoformat(str(v)[:10])


def _eq(a, b, p):
    return round(_f(a), p) == round(_f(b), p)


def _s(v):
    return (v or "").strip() if isinstance(v, str) or v is None else str(v)


def _norm_text(v):
    return " ".join(_s(v).split())


def match_items(orig, repl):
    """Returns (pairs[(oi, rj, basis)], unresolved_o, unresolved_r, removed, added) as index lists."""
    pairs = []
    un_o, un_r = list(range(len(orig))), list(range(len(repl)))

    # Step 1: unique (MR, MR item, item code) on both sides
    def k1(x):
        if x.get("material_request") and x.get("material_request_item") and x.get("item_code"):
            return (x["material_request"], x["material_request_item"], x["item_code"])
        return None

    co, cr = defaultdict(list), defaultdict(list)
    for i in un_o:
        k = k1(orig[i])
        if k:
            co[k].append(i)
    for j in un_r:
        k = k1(repl[j])
        if k:
            cr[k].append(j)
    for k, ois in co.items():
        rjs = cr.get(k)
        if rjs and len(ois) == 1 and len(rjs) == 1:
            pairs.append((ois[0], rjs[0], "MR Item"))
    mo, mr = {p[0] for p in pairs}, {p[1] for p in pairs}
    un_o = [i for i in un_o if i not in mo]
    un_r = [j for j in un_r if j not in mr]

    # Step 2: item code that occurs exactly once on each remaining side
    go, gr = defaultdict(list), defaultdict(list)
    for i in un_o:
        if orig[i].get("item_code"):
            go[orig[i]["item_code"]].append(i)
    for j in un_r:
        if repl[j].get("item_code"):
            gr[repl[j]["item_code"]].append(j)
    for item, ois in go.items():
        rjs = gr.get(item)
        if rjs and len(ois) == 1 and len(rjs) == 1:
            pairs.append((ois[0], rjs[0], "Unique Item"))
    mo, mr = {p[0] for p in pairs}, {p[1] for p in pairs}
    un_o = [i for i in un_o if i not in mo]
    un_r = [j for j in un_r if j not in mr]

    # Step 3: item present on both remaining sides but not 1:1 -> Unresolved; otherwise Added / Removed
    r_items = {repl[j].get("item_code") for j in un_r if repl[j].get("item_code")}
    o_items = {orig[i].get("item_code") for i in un_o if orig[i].get("item_code")}
    unresolved_o = [i for i in un_o if orig[i].get("item_code") in r_items]
    unresolved_r = [j for j in un_r if repl[j].get("item_code") in o_items]
    removed = [i for i in un_o if i not in set(unresolved_o)]
    added = [j for j in un_r if j not in set(unresolved_r)]
    return pairs, unresolved_o, unresolved_r, removed, added


def _mr_ref(o, r):
    refs = []
    for row in (o, r):
        if row and row.get("material_request"):
            ref = row["material_request"] + (" / " + row["material_request_item"] if row.get("material_request_item") else "")
            if ref not in refs:
                refs.append(ref)
    return " | ".join(refs)


def _blank_row():
    return {
        "match_status": "", "match_basis": "", "item_code": "", "replacement_item_code": "", "item_name": "",
        "mr_reference": "", "original_uom": "", "replacement_uom": "",
        "original_qty": 0.0, "replacement_qty": 0.0, "qty_difference": 0.0, "qty_comparable": 0,
        "original_rate": 0.0, "replacement_rate": 0.0, "rate_difference": 0.0, "rate_comparable": 0,
        "original_amount": 0.0, "replacement_amount": 0.0, "amount_difference": 0.0, "amount_comparable": 0,
        "original_delivery_date": None, "replacement_delivery_date": None, "delivery_days_difference": 0,
        "is_comparable": 0, "comparison_flags": "", "original_description": "", "replacement_description": "",
        "original_po_detail": "", "replacement_po_detail": "",
    }


def compare_items(orig, repl, same_currency=True, qty_prec=3, amt_prec=2):
    pairs, un_o, un_r, removed, added = match_items(orig, repl)
    entries = []
    rate_benefit, eligible, n_changed = 0.0, 0, 0
    n_uom = n_spec = n_lineage = n_missing_date = n_fallback = 0

    for i, j, basis in pairs:
        o, r = orig[i], repl[j]
        flags = []
        same_uom = _s(o.get("uom")) == _s(r.get("uom"))
        qty_c, rate_c, amt_c = same_uom, same_uom and same_currency, same_currency
        spec_diff = _norm_text(o.get("description")) != _norm_text(r.get("description"))
        lineage_diff = (_s(o.get("material_request")), _s(o.get("material_request_item"))) != (
            _s(r.get("material_request")), _s(r.get("material_request_item")))
        if basis == "Unique Item":
            n_fallback += 1
            flags.append("Matched on unique item code only (not MR item)" + ("; MR lineage differs" if lineage_diff else ""))
        elif lineage_diff:
            flags.append("MR lineage differs")
        if lineage_diff:
            n_lineage += 1
        if not same_uom:
            n_uom += 1
            flags.append("UOM changed (%s -> %s): quantity and rate not comparable" % (o.get("uom"), r.get("uom")))
        if not same_currency:
            flags.append("Currency changed: rate and amount not comparable")
        if spec_diff:
            n_spec += 1
            flags.append("Specification / description differs")
        od, rd = _d(o.get("schedule_date")), _d(r.get("schedule_date"))
        if not (od and rd):
            n_missing_date += 1
            flags.append("Missing Date")
        qo, qr = _f(o.get("qty")), _f(r.get("qty"))
        ro, rr = _f(o.get("rate")), _f(r.get("rate"))
        ao, ar = _f(o.get("amount")), _f(r.get("amount"))
        changed = (
            spec_diff or not same_uom or not same_currency or lineage_diff
            or (qty_c and not _eq(qo, qr, qty_prec))
            or (rate_c and not _eq(ro, rr, qty_prec))
            or (amt_c and not _eq(ao, ar, amt_prec))
            or (od and rd and od != rd)
        )
        if rate_c:
            eligible += 1
            rate_benefit += (ro - rr) * qr
        if changed:
            n_changed += 1
        row = _blank_row()
        row.update({
            "match_status": "Changed" if changed else "Unchanged", "match_basis": basis,
            "item_code": o.get("item_code"), "replacement_item_code": r.get("item_code"),
            "item_name": r.get("item_name") or o.get("item_name"), "mr_reference": _mr_ref(o, r),
            "original_uom": o.get("uom"), "replacement_uom": r.get("uom"),
            "original_qty": qo, "replacement_qty": qr, "qty_difference": (qr - qo) if qty_c else 0.0, "qty_comparable": int(qty_c),
            "original_rate": ro, "replacement_rate": rr, "rate_difference": (rr - ro) if rate_c else 0.0, "rate_comparable": int(rate_c),
            "original_amount": ao, "replacement_amount": ar, "amount_difference": (ar - ao) if amt_c else 0.0, "amount_comparable": int(amt_c),
            "original_delivery_date": od, "replacement_delivery_date": rd,
            "delivery_days_difference": (rd - od).days if (od and rd) else 0,
            "is_comparable": int(qty_c and rate_c and amt_c and bool(od and rd)),
            "comparison_flags": "\n".join(flags),
            "original_description": _norm_text(o.get("description")), "replacement_description": _norm_text(r.get("description")),
            "original_po_detail": o.get("po_detail"), "replacement_po_detail": r.get("po_detail"),
        })
        entries.append(((i, 0), row))

    # possible substitution: same MR item, different item code, on leftover rows
    rem_by_mri = defaultdict(list)
    for i in removed:
        if orig[i].get("material_request_item"):
            rem_by_mri[orig[i]["material_request_item"]].append(("o", orig[i]))
    for j in added:
        if repl[j].get("material_request_item"):
            rem_by_mri[repl[j]["material_request_item"]].append(("r", repl[j]))

    def subst_flag(row, side):
        mri = row.get("material_request_item")
        for s, other in rem_by_mri.get(mri, []):
            if s != side and other.get("item_code") != row.get("item_code"):
                a, b = (row, other) if side == "o" else (other, row)
                return "Possible substitution on MR item %s (%s -> %s); items are not treated as equivalent" % (mri, a.get("item_code"), b.get("item_code"))
        return ""

    for i in removed:
        o = orig[i]
        qo, ao = _f(o.get("qty")), _f(o.get("amount"))
        row = _blank_row()
        flags = ["Removed: not present in replacement PO", "Scope delta uses a zero baseline", "Rate and delivery comparison N/A"]
        sf = subst_flag(o, "o")
        if sf:
            flags.append(sf)
        row.update({
            "match_status": "Removed", "item_code": o.get("item_code"), "item_name": o.get("item_name"),
            "mr_reference": _mr_ref(o, None), "original_uom": o.get("uom"),
            "original_qty": qo, "qty_difference": -qo, "qty_comparable": 1,
            "original_rate": _f(o.get("rate")), "original_amount": ao,
            "amount_difference": -ao if same_currency else 0.0, "amount_comparable": int(same_currency),
            "original_delivery_date": _d(o.get("schedule_date")), "comparison_flags": "\n".join(flags),
            "original_description": _norm_text(o.get("description")), "original_po_detail": o.get("po_detail"),
        })
        entries.append(((i, 0), row))
    for j in added:
        r = repl[j]
        qr, ar = _f(r.get("qty")), _f(r.get("amount"))
        row = _blank_row()
        flags = ["Added: not present in original PO", "Scope delta uses a zero baseline", "Rate and delivery comparison N/A"]
        sf = subst_flag(r, "r")
        if sf:
            flags.append(sf)
        row.update({
            "match_status": "Added", "item_code": r.get("item_code"), "replacement_item_code": r.get("item_code"),
            "item_name": r.get("item_name"), "mr_reference": _mr_ref(None, r), "replacement_uom": r.get("uom"),
            "replacement_qty": qr, "qty_difference": qr, "qty_comparable": 1,
            "replacement_rate": _f(r.get("rate")), "replacement_amount": ar,
            "amount_difference": ar if same_currency else 0.0, "amount_comparable": int(same_currency),
            "replacement_delivery_date": _d(r.get("schedule_date")), "comparison_flags": "\n".join(flags),
            "replacement_description": _norm_text(r.get("description")), "replacement_po_detail": r.get("po_detail"),
        })
        entries.append(((len(orig) + j, 1), row))

    for i in un_o:
        o = orig[i]
        row = _blank_row()
        row.update({
            "match_status": "Unresolved", "match_basis": "Unresolved (repeated item, no unique lineage)",
            "item_code": o.get("item_code"), "item_name": o.get("item_name"), "mr_reference": _mr_ref(o, None),
            "original_uom": o.get("uom"), "original_qty": _f(o.get("qty")), "original_rate": _f(o.get("rate")),
            "original_amount": _f(o.get("amount")), "original_delivery_date": _d(o.get("schedule_date")),
            "comparison_flags": "Unresolved: original PO row of repeated item %s could not be paired reliably; all differences N/A" % o.get("item_code"),
            "original_description": _norm_text(o.get("description")), "original_po_detail": o.get("po_detail"),
        })
        entries.append(((i, 0), row))
    for j in un_r:
        r = repl[j]
        row = _blank_row()
        row.update({
            "match_status": "Unresolved", "match_basis": "Unresolved (repeated item, no unique lineage)",
            "item_code": r.get("item_code"), "replacement_item_code": r.get("item_code"), "item_name": r.get("item_name"),
            "mr_reference": _mr_ref(None, r), "replacement_uom": r.get("uom"), "replacement_qty": _f(r.get("qty")),
            "replacement_rate": _f(r.get("rate")), "replacement_amount": _f(r.get("amount")),
            "replacement_delivery_date": _d(r.get("schedule_date")),
            "comparison_flags": "Unresolved: replacement PO row of repeated item %s could not be paired reliably; all differences N/A" % r.get("item_code"),
            "replacement_description": _norm_text(r.get("description")), "replacement_po_detail": r.get("po_detail"),
        })
        entries.append(((len(orig) + j, 1), row))

    entries.sort(key=lambda e: e[0])
    unresolved = len(un_o) + len(un_r)
    if eligible == 0:
        coverage = "Not Comparable"
    elif eligible == len(pairs) and unresolved == 0:
        coverage = "Complete"
    else:
        coverage = "Partial"
    return {
        "rows": [e[1] for e in entries],
        "rate_benefit": rate_benefit if eligible else 0.0,
        "rate_benefit_status": coverage,
        "items_added": len(added), "items_removed": len(removed),
        "items_changed": n_changed, "items_unresolved": unresolved,
        "uom_diff_count": n_uom, "spec_diff_count": n_spec, "lineage_diff_count": n_lineage,
        "missing_date_count": n_missing_date, "fallback_count": n_fallback,
    }


def compare_mr(orig, repl):
    def info(rows):
        mrs, items, missing = set(), set(), []
        for r in rows:
            if r.get("material_request"):
                mrs.add(r["material_request"])
                items.add((r["material_request"], r.get("material_request_item") or ""))
            else:
                missing.append(r)
        return mrs, items, missing

    om, oi, omiss = info(orig)
    rm, ri, rmiss = info(repl)
    lines = [
        "Original PO MRs: %s" % (", ".join(sorted(om)) or "none"),
        "Replacement PO MRs: %s" % (", ".join(sorted(rm)) or "none"),
    ]
    if om - rm:
        lines.append("Only on original PO: %s" % ", ".join(sorted(om - rm)))
    if rm - om:
        lines.append("Only on replacement PO: %s" % ", ".join(sorted(rm - om)))
    for side, miss in (("Original", omiss), ("Replacement", rmiss)):
        if miss:
            lines.append("%s PO rows without MR (%d): %s" % (side, len(miss), ", ".join("%s [%s]" % (m.get("item_code"), m.get("po_detail")) for m in miss[:10]) + (" ..." if len(miss) > 10 else "")))
    lineage = om == rm and oi != ri
    if lineage:
        lines.append("Same MR documents, but different MR item rows are referenced (%d only on original, %d only on replacement)." % (len(oi - ri), len(ri - oi)))
    if not om or not rm or omiss or rmiss:
        status = "Missing"
    elif om == rm:
        status = "Match"
    else:
        status = "Mismatch"
    return {"status": status, "summary": "\n".join(lines), "lineage_diff": lineage}
