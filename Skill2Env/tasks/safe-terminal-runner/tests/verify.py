#!/usr/bin/env python3
"""Deterministic verifier for the storefront DB-repair task.

Run from the solver's final workspace:  python3 verify.py
Prints exactly one JSON line and always exits 0.
"""
import json, os, re, sqlite3, sys

# ---------------------------------------------------------------- GT (author-only)
GT = {'norm': ['SKU-1001', 'SKU-1002', 'SKU-1007', 'SKU-1008', 'SKU-1011', 'SKU-1013', 'SKU-1015', 'SKU-1019', 'SKU-1022'], 'clamp': ['SKU-1002', 'SKU-1008', 'SKU-1016'], 'deact': ['SKU-1004', 'SKU-1007', 'SKU-1017'], 'applied': ['SKU-1005', 'SKU-1006', 'SKU-1012'], 'inv': 16225.19, 'products': [['SKU-1001', 'Men\'s "Classic" 100% Cotton Tee', 25.99, 'usd', 34, 1], ['SKU-1002', "O'Malley's Irish Stout Brewing Kit", 18.99, 'usd', 0, 1], ['SKU-1003', '50% Off Clearance Mug', 499.0, 'usd', 12, 1], ['SKU-1004', '[DISCONTINUED] Legacy USB Charger', 19.99, 'usd', 40, 0], ['SKU-1005', 'Widget "Pro" 2000', 39.99, 'usd', 7, 1], ['SKU-1006', 'Basic Widget', 8.99, 'usd', 100, 1], ['SKU-1007', '[DISCONTINUED] Dock "V1" 25% Kit', 79.99, 'usd', 5, 0], ['SKU-1008', 'Gourmet 25% Cocoa Bar', 3.5, 'usd', 0, 1], ['SKU-1009', "Stoner's $5 Coupon Guide", 7.5, 'usd', 22, 1], ['SKU-1010', 'Trail Mix (Family Size)', 14.25, 'usd', 61, 1], ['SKU-1011', 'Ceramic Pour-Over Dripper', 22.99, 'usd', 18, 1], ['SKU-1012', "Travel Journal 'Wanderer'", 14.5, 'usd', 45, 1], ['SKU-1013', 'Bamboo Cutting Board', 18.99, 'usd', 0, 1], ['SKU-1014', 'Noise-Cancel Earbuds', 59.95, 'usd', 9, 1], ['SKU-1015', 'Cast Iron Skillet 10in', 24.99, 'usd', 14, 1], ['SKU-1016', 'Organic Green Tea 100ct', 11.2, 'usd', 0, 1], ['SKU-1017', '[DISCONTINUED] Flip Phone Case', 4.75, 'usd', 3, 0], ['SKU-1018', 'Stainless Water Bottle 750ml', 17.99, 'usd', 80, 1], ['SKU-1019', 'Desk Lamp "Halo" Mini', 32.99, 'usd', 26, 1], ['SKU-1020', 'Yoga Mat 6mm', 21.5, 'usd', 33, 1], ['SKU-1021', "Chef's Knife 8in", 44.0, 'usd', 11, 1], ['SKU-1022', 'LED Strip 5m (RGB)', 15.99, 'usd', 52, 1], ['SKU-1023', 'Linen Throw Pillow', 13.8, 'usd', 29, 1], ['SKU-1024', 'Pocket Notebook 3-Pack 100% Recycled', 6.25, 'usd', 74, 1]], 'orders': [[1, 'SKU-1021', 1, 504, '2024-05-17'], [2, 'SKU-1008', 2, 1139, '2024-09-12'], [3, 'SKU-1019', 4, 560, '2024-01-12'], [4, 'SKU-1007', 2, 4439, '2024-01-27'], [5, 'SKU-1007', 5, 3736, '2024-04-24'], [6, 'SKU-1019', 3, 353, '2024-03-23'], [7, 'SKU-1011', 3, 1573, '2024-04-20'], [8, 'SKU-1004', 1, 3412, '2024-02-21'], [9, 'SKU-1012', 5, 2466, '2024-01-24'], [10, 'SKU-1018', 1, 3400, '2024-02-27'], [11, 'SKU-1010', 5, 3262, '2024-04-12'], [12, 'SKU-1002', 2, 2670, '2024-02-17'], [13, 'SKU-1004', 4, 2577, '2024-08-21'], [14, 'SKU-1006', 3, 3210, '2024-04-18'], [15, 'SKU-1023', 1, 5290, '2024-03-27'], [16, 'SKU-1024', 2, 1638, '2024-08-22'], [17, 'SKU-1009', 5, 2099, '2024-06-11'], [18, 'SKU-1008', 1, 2884, '2024-07-18'], [19, 'SKU-1003', 2, 4946, '2024-06-16'], [20, 'SKU-1021', 4, 3541, '2024-08-14'], [21, 'SKU-1009', 2, 2320, '2024-09-27'], [22, 'SKU-1009', 5, 3809, '2024-07-21'], [23, 'SKU-1008', 2, 4474, '2024-08-12'], [24, 'SKU-1002', 1, 1552, '2024-03-23'], [25, 'SKU-1020', 1, 3452, '2024-07-24'], [26, 'SKU-1017', 3, 4832, '2024-01-13'], [27, 'SKU-1022', 5, 2485, '2024-06-13'], [28, 'SKU-1010', 4, 1595, '2024-08-10'], [29, 'SKU-1024', 3, 4400, '2024-03-26'], [30, 'SKU-1004', 3, 5534, '2024-09-16'], [31, 'SKU-1005', 3, 1623, '2024-09-26'], [32, 'SKU-1001', 5, 2955, '2024-08-10'], [33, 'SKU-1004', 3, 2819, '2024-04-11'], [34, 'SKU-1008', 5, 945, '2024-02-25'], [35, 'SKU-1003', 5, 1330, '2024-03-25'], [36, 'SKU-1018', 2, 2471, '2024-09-23'], [37, 'SKU-1007', 5, 5951, '2024-04-19'], [38, 'SKU-1013', 3, 3888, '2024-09-24'], [39, 'SKU-1004', 2, 2140, '2024-02-20'], [40, 'SKU-1001', 5, 4837, '2024-04-28']], 'schema_products': "CREATE TABLE products(\n  sku TEXT PRIMARY KEY,\n  name TEXT NOT NULL,\n  price REAL NOT NULL,\n  price_unit TEXT NOT NULL CHECK(price_unit IN ('usd','cents')),\n  stock INTEGER NOT NULL,\n  active INTEGER NOT NULL DEFAULT 1)", 'schema_orders': 'CREATE TABLE orders(\n  order_id INTEGER PRIMARY KEY,\n  sku TEXT NOT NULL,\n  qty INTEGER NOT NULL,\n  unit_price_cents INTEGER NOT NULL,\n  order_date TEXT NOT NULL)'}

IGNORE_DIRS = {"_skill_ref", "_eval", "task_inputs", ".pi", "__pycache__", ".git"}
IGNORE_FILES = {"pi-tools-ext.ts", ".serper_key", ".teich-prompt.txt",
                "verify.py", "eval_spec.json", "task_blueprint.json", "setup.sh"}


def _approx(a, b, tol=0.005):
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return False


def _norm_sku_list(v):
    try:
        return sorted(str(s).strip().upper() for s in v)
    except Exception:
        return None


def check_prices():
    """R1: price normalization + corrections precedence on the products table."""
    try:
        con = sqlite3.connect("shop.db"); cur = con.cursor()
        rows = {r[0]: list(r[1:]) for r in cur.execute(
            "SELECT sku,name,price,price_unit,stock,active FROM products")}
        con.close()
    except Exception as e:
        return 0.0, f"cannot read shop.db: {e}"
    exp = {r[0]: r[1:] for r in GT["products"]}
    subs = []
    # all expected SKUs present, no extras
    ok = set(rows) == set(exp)
    subs.append(1.0 if ok else 0.0)
    if not ok:
        return 0.0, f"SKU set mismatch: missing={sorted(set(exp)-set(rows))} extra={sorted(set(rows)-set(exp))}"
    # per-SKU price check (the heart of R1: precedence + normalization)
    bad = [s for s in exp if not _approx(rows[s][1], exp[s][1], 0.005)]
    price_score = 1.0 - len(bad) / len(exp)
    subs.append(max(price_score, 0.0))
    # every price_unit must be 'usd'
    units_ok = all(rows[s][2] == "usd" for s in exp)
    subs.append(1.0 if units_ok else 0.0)
    # precedence-critical probe: SKU-1005 must be 39.99 (correction), not 45.99
    subs.append(1.0 if _approx(rows["SKU-1005"][1], 39.99, 0.005) else 0.0)
    # names must be preserved
    names_ok = all(rows[s][0] == exp[s][0] for s in exp)
    subs.append(1.0 if names_ok else 0.0)
    score = sum(subs) / len(subs)
    detail = "prices ok" if score == 1.0 else f"bad prices: {bad[:6]}; units_ok={units_ok}; names_ok={names_ok}"
    return score, detail


def check_stock_status_preservation():
    """R2: stock clamps, deactivations, unaffected rows, orders ledger, schema."""
    subs, msgs = [], []
    try:
        con = sqlite3.connect("shop.db"); cur = con.cursor()
        prods = {r[0]: list(r[1:]) for r in cur.execute(
            "SELECT sku,name,price,price_unit,stock,active FROM products")}
        orders = sorted(map(list, cur.execute("SELECT * FROM orders")))
        schemas = {r[0]: r[1] for r in cur.execute(
            "SELECT name, sql FROM sqlite_master WHERE type='table'")}
        con.close()
    except Exception as e:
        return 0.0, f"cannot read shop.db: {e}"
    exp = {r[0]: r[1:] for r in GT["products"]}
    # stock values
    bad_stock = [s for s in exp if prods.get(s, [None] * 5)[3] != exp[s][3]]
    subs.append(1.0 - len(bad_stock) / len(exp)); msgs.append(f"bad_stock={bad_stock[:5]}")
    # active flags
    bad_act = [s for s in exp if prods.get(s, [None]*5)[4] != exp[s][4]]
    subs.append(1.0 - len(bad_act) / len(exp)); msgs.append(f"bad_active={bad_act[:5]}")
    # orders untouched (full row-set comparison)
    orders_ok = orders == sorted(map(list, GT["orders"])) or orders == sorted(map(lambda r: list(map(str, r)), GT["orders"]))
    subs.append(1.0 if orders_ok else 0.0); msgs.append(f"orders_ok={orders_ok} (n={len(orders)})")
    # schema preserved (CHECK constraint intact)
    try:
        sch = re.sub(r"\s+", " ", schemas.get("products", "")).strip()
        exp_sch = re.sub(r"\s+", " ", GT["schema_products"]).strip()
        subs.append(1.0 if sch == exp_sch else (0.5 if "CHECK" in sch.upper() else 0.0))
    except Exception:
        subs.append(0.0)
    score = sum(subs) / len(subs)
    return score, "; ".join(msgs) if score < 1.0 else "stock/status/preservation ok"


def check_report():
    """R3: audit_report.json schema, per-class counts/SKUs, inventory value."""
    try:
        with open("audit_report.json") as f:
            rep = json.load(f)
    except Exception as e:
        return 0.0, f"cannot read audit_report.json: {e}"
    subs, msgs = [], []
    expected = {
        "price_normalizations": GT["norm"],
        "stock_clamps": GT["clamp"],
        "deactivations": GT["deact"],
        "corrections_applied": GT["applied"],
    }
    for key, exp_skus in expected.items():
        sec = rep.get(key)
        if not isinstance(sec, dict):
            subs.append(0.0); msgs.append(f"{key} missing/not object"); continue
        skus = _norm_sku_list(sec.get("skus"))
        count_ok = isinstance(sec.get("count"), int) and sec["count"] == len(exp_skus)
        skus_ok = skus == exp_skus
        # count must also agree with the reported sku list
        consistent = count_ok and isinstance(sec.get("skus"), list) and len(sec["skus"]) == sec["count"]
        subs.append((0.5 if count_ok else 0.0) + (0.5 if skus_ok else 0.0))
        if not (count_ok and skus_ok and consistent):
            msgs.append(f"{key}: count_ok={count_ok} skus_ok={skus_ok}")
    inv = rep.get("inventory_value_usd")
    try:
        inv_ok = _approx(float(inv), GT["inv"], 0.011)
    except Exception:
        inv_ok = False
    subs.append(1.0 if inv_ok else 0.0)
    if not inv_ok:
        msgs.append(f"inventory_value_usd={inv!r}, expected {GT['inv']}")
    # cross-check report against the actual repaired DB
    try:
        con = sqlite3.connect("shop.db")
        db_inv = round(sum(p * s for p, s in con.execute(
            "SELECT price, stock FROM products WHERE active=1")), 2)
        con.close()
        subs.append(1.0 if _approx(db_inv, float(inv or 0), 0.011) else 0.0)
    except Exception as e:
        subs.append(0.0); msgs.append(f"db cross-check failed: {e}")
    score = sum(subs) / len(subs)
    return score, "report ok" if score == 1.0 else "; ".join(msgs) or "report partial"


def check_hygiene():
    """R4: no temp_* leftovers; .gitignore covers temp_*."""
    subs, msgs = [], []
    leftovers = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for fn in files:
            if fn in IGNORE_FILES:
                continue
            if os.path.basename(fn).startswith("temp_"):
                leftovers.append(os.path.join(root, fn))
    subs.append(1.0 if not leftovers else 0.0)
    if leftovers:
        msgs.append(f"temp_* leftovers: {leftovers[:5]}")
    try:
        gi = open(".gitignore").read()
        covered = any(re.fullmatch(r"\s*temp_.*\s*", ln) or re.fullmatch(r"\s*\**/temp_\*.*\s*", ln)
                      for ln in gi.splitlines())
    except Exception:
        covered = False
    subs.append(1.0 if covered else 0.0)
    if not covered:
        msgs.append(".gitignore lacks a temp_* entry")
    score = sum(subs) / len(subs)
    return score, "hygiene ok" if score == 1.0 else "; ".join(msgs)


CHECKS = [
    ("db_price_repairs", 0.30, check_prices),
    ("db_stock_status_preservation", 0.25, check_stock_status_preservation),
    ("audit_report", 0.30, check_report),
    ("workspace_hygiene", 0.15, check_hygiene),
]


def main():
    per_item, checks, total_w, acc = {}, [], 0.0, 0.0
    for cid, w, fn in CHECKS:
        try:
            s, detail = fn()
        except Exception as e:  # a failed check scores 0 but never kills the run
            s, detail = 0.0, f"check crashed: {e}"
        s = max(0.0, min(1.0, float(s)))
        per_item[cid] = round(s, 4)
        checks.append({"id": cid, "weight": w, "score": round(s, 4), "detail": detail})
        total_w += w
        acc += w * s
    final = round(acc / total_w, 4) if total_w else 1.0
    print(json.dumps({"per_item": per_item, "checks": checks, "score": final}))


if __name__ == "__main__":
    main()
