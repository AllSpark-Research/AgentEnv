#!/usr/bin/env python3
"""Deterministic verifier for the ShopFlow order-feed cleanup task.
Run: python3 verify.py   (cwd = solver's final workspace)
Prints exactly one JSON line per the harness contract."""
import csv, json, hashlib
from decimal import Decimal, InvalidOperation

EXPECTED = {
  "clean_headers": [
    "order_id",
    "order_date",
    "customer_name",
    "customer_email",
    "sku",
    "quantity",
    "unit_price_usd",
    "status",
    "region"
  ],
  "clean_rows": [
    {
      "order_id": "ORD-1001",
      "order_date": "2024-03-06",
      "customer_name": "Ren\u00e9e Lef\u00e8vre",
      "customer_email": "renee.lefevre@example.com",
      "sku": "SKU-101",
      "quantity": "2",
      "unit_price_usd": "29.99",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1002",
      "order_date": "2024-03-07",
      "customer_name": "Marcus Webb",
      "customer_email": "marcus.webb@example.com",
      "sku": "SKU-102",
      "quantity": "3",
      "unit_price_usd": "23.81",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1003",
      "order_date": "2024-03-08",
      "customer_name": "Aisha Khan",
      "customer_email": "aisha.khan@example.com",
      "sku": "SKU-103",
      "quantity": "4",
      "unit_price_usd": "10.25",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1004",
      "order_date": "2024-03-09",
      "customer_name": "Tom Becker",
      "customer_email": "tom.becker@example.com",
      "sku": "SKU-104",
      "quantity": "5",
      "unit_price_usd": "74.93",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1005",
      "order_date": "2024-03-10",
      "customer_name": "",
      "customer_email": "lucia.fernandez@example.com",
      "sku": "SKU-105",
      "quantity": "1",
      "unit_price_usd": "67.46",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1006",
      "order_date": "2024-03-11",
      "customer_name": "Jonah Reyes",
      "customer_email": "jonah.reyes@example.com",
      "sku": "SKU-106",
      "quantity": "2",
      "unit_price_usd": "91.31",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1007",
      "order_date": "2024-03-12",
      "customer_name": "Priya Nair",
      "customer_email": "priya.nair@example.com",
      "sku": "SKU-107",
      "quantity": "3",
      "unit_price_usd": "1183.68",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1008",
      "order_date": "2024-03-13",
      "customer_name": "Ole Bj\u00f8rnson",
      "customer_email": "ole.bjrnson@example.com",
      "sku": "SKU-108",
      "quantity": "4",
      "unit_price_usd": "148.58",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1009",
      "order_date": "2024-03-14",
      "customer_name": "Hana Sato",
      "customer_email": "hana.sato@example.com",
      "sku": "SKU-101",
      "quantity": "5",
      "unit_price_usd": "28.49",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1010",
      "order_date": "2024-03-15",
      "customer_name": "Diego Mar\u00edn",
      "customer_email": "diego.marin@example.com",
      "sku": "SKU-102",
      "quantity": "1",
      "unit_price_usd": "26.46",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1011",
      "order_date": "2024-03-16",
      "customer_name": "",
      "customer_email": "emma.clark@example.com",
      "sku": "SKU-103",
      "quantity": "2",
      "unit_price_usd": "9.71",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1012",
      "order_date": "2024-03-17",
      "customer_name": "Fran\u00e7ois Moreau",
      "customer_email": "francois.moreau@example.com",
      "sku": "SKU-104",
      "quantity": "3",
      "unit_price_usd": "71.18",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1013",
      "order_date": "2024-03-18",
      "customer_name": "Sofia Rossi",
      "customer_email": "sofia.rossi@example.com",
      "sku": "SKU-105",
      "quantity": "4",
      "unit_price_usd": "74.95",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1014",
      "order_date": "2024-03-19",
      "customer_name": "Jan Kowalski",
      "customer_email": "jan.kowalski@example.com",
      "sku": "SKU-106",
      "quantity": "5",
      "unit_price_usd": "86.51",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1015",
      "order_date": "2024-03-20",
      "customer_name": "Mei Lin",
      "customer_email": "mei.lin@example.com",
      "sku": "SKU-107",
      "quantity": "1",
      "unit_price_usd": "35.14",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1016",
      "order_date": "2024-03-21",
      "customer_name": "Omar Haddad",
      "customer_email": "omar.haddad@example.com",
      "sku": "SKU-108",
      "quantity": "2",
      "unit_price_usd": "165.09",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1017",
      "order_date": "2024-03-22",
      "customer_name": "",
      "customer_email": "grace.oneill@example.com",
      "sku": "SKU-101",
      "quantity": "3",
      "unit_price_usd": "449.85",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1018",
      "order_date": "2024-03-23",
      "customer_name": "Viktor Petrov",
      "customer_email": "viktor.petrov@example.com",
      "sku": "SKU-102",
      "quantity": "4",
      "unit_price_usd": "25.14",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1019",
      "order_date": "2024-03-24",
      "customer_name": "Nina Berger",
      "customer_email": "nina.berger@example.com",
      "sku": "SKU-103",
      "quantity": "5",
      "unit_price_usd": "10.79",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1020",
      "order_date": "2024-03-25",
      "customer_name": "Elif Y\u0131lmaz",
      "customer_email": "elif.ylmaz@example.com",
      "sku": "SKU-104",
      "quantity": "1",
      "unit_price_usd": "67.44",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1021",
      "order_date": "2024-03-26",
      "customer_name": "Ren\u00e9e Lef\u00e8vre",
      "customer_email": "renee.lefevre@example.com",
      "sku": "SKU-105",
      "quantity": "2",
      "unit_price_usd": "71.20",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1022",
      "order_date": "2024-03-27",
      "customer_name": "Marcus Webb",
      "customer_email": "marcus.webb@example.com",
      "sku": "SKU-106",
      "quantity": "3",
      "unit_price_usd": "96.12",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1023",
      "order_date": "2024-03-28",
      "customer_name": "",
      "customer_email": "aisha.khan@example.com",
      "sku": "SKU-107",
      "quantity": "4",
      "unit_price_usd": "33.30",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1024",
      "order_date": "2024-03-29",
      "customer_name": "Tom Becker",
      "customer_email": "tom.becker@example.com",
      "sku": "SKU-108",
      "quantity": "5",
      "unit_price_usd": "156.83",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1025",
      "order_date": "2024-03-30",
      "customer_name": "Luc\u00eda Fern\u00e1ndez",
      "customer_email": "lucia.fernandez@example.com",
      "sku": "SKU-101",
      "quantity": "1",
      "unit_price_usd": "29.99",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1026",
      "order_date": "2024-03-31",
      "customer_name": "Jonah Reyes",
      "customer_email": "jonah.reyes@example.com",
      "sku": "SKU-102",
      "quantity": "2",
      "unit_price_usd": "23.81",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1027",
      "order_date": "2024-04-01",
      "customer_name": "Priya Nair",
      "customer_email": "priya.nair@example.com",
      "sku": "SKU-103",
      "quantity": "3",
      "unit_price_usd": "345.25",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1028",
      "order_date": "2024-04-02",
      "customer_name": "Ole Bj\u00f8rnson",
      "customer_email": "ole.bjrnson@example.com",
      "sku": "SKU-104",
      "quantity": "4",
      "unit_price_usd": "74.93",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1029",
      "order_date": "2024-04-03",
      "customer_name": "",
      "customer_email": "hana.sato@example.com",
      "sku": "SKU-105",
      "quantity": "5",
      "unit_price_usd": "67.46",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1030",
      "order_date": "2024-04-04",
      "customer_name": "Diego Mar\u00edn",
      "customer_email": "diego.marin@example.com",
      "sku": "SKU-106",
      "quantity": "1",
      "unit_price_usd": "91.31",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1031",
      "order_date": "2024-04-05",
      "customer_name": "Emma Clark",
      "customer_email": "emma.clark@example.com",
      "sku": "SKU-107",
      "quantity": "2",
      "unit_price_usd": "36.99",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1032",
      "order_date": "2024-04-06",
      "customer_name": "Fran\u00e7ois Moreau",
      "customer_email": "francois.moreau@example.com",
      "sku": "SKU-108",
      "quantity": "3",
      "unit_price_usd": "148.58",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1033",
      "order_date": "2024-04-07",
      "customer_name": "Sofia Rossi",
      "customer_email": "sofia.rossi@example.com",
      "sku": "SKU-101",
      "quantity": "4",
      "unit_price_usd": "28.49",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1034",
      "order_date": "2024-04-08",
      "customer_name": "Jan Kowalski",
      "customer_email": "jan.kowalski@example.com",
      "sku": "SKU-102",
      "quantity": "5",
      "unit_price_usd": "26.46",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1035",
      "order_date": "2024-04-09",
      "customer_name": "",
      "customer_email": "mei.lin@example.com",
      "sku": "SKU-103",
      "quantity": "1",
      "unit_price_usd": "9.71",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1036",
      "order_date": "2024-04-10",
      "customer_name": "Omar Haddad",
      "customer_email": "omar.haddad@example.com",
      "sku": "SKU-104",
      "quantity": "2",
      "unit_price_usd": "71.18",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1037",
      "order_date": "2024-04-11",
      "customer_name": "Grace O'Neill",
      "customer_email": "grace.oneill@example.com",
      "sku": "SKU-105",
      "quantity": "3",
      "unit_price_usd": "1124.25",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1038",
      "order_date": "2024-04-12",
      "customer_name": "Viktor Petrov",
      "customer_email": "viktor.petrov@example.com",
      "sku": "SKU-106",
      "quantity": "4",
      "unit_price_usd": "86.51",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1039",
      "order_date": "2024-04-13",
      "customer_name": "Nina Berger",
      "customer_email": "nina.berger@example.com",
      "sku": "SKU-107",
      "quantity": "5",
      "unit_price_usd": "35.14",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1040",
      "order_date": "2024-04-14",
      "customer_name": "Elif Y\u0131lmaz",
      "customer_email": "elif.ylmaz@example.com",
      "sku": "SKU-108",
      "quantity": "1",
      "unit_price_usd": "165.09",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1041",
      "order_date": "2024-04-15",
      "customer_name": "",
      "customer_email": "renee.lefevre@example.com",
      "sku": "SKU-101",
      "quantity": "2",
      "unit_price_usd": "26.99",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1042",
      "order_date": "2024-04-16",
      "customer_name": "Marcus Webb",
      "customer_email": "marcus.webb@example.com",
      "sku": "SKU-102",
      "quantity": "3",
      "unit_price_usd": "25.14",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1043",
      "order_date": "2024-04-17",
      "customer_name": "Aisha Khan",
      "customer_email": "aisha.khan@example.com",
      "sku": "SKU-103",
      "quantity": "4",
      "unit_price_usd": "10.79",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1044",
      "order_date": "2024-04-18",
      "customer_name": "Tom Becker",
      "customer_email": "tom.becker@example.com",
      "sku": "SKU-104",
      "quantity": "5",
      "unit_price_usd": "67.44",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1045",
      "order_date": "2024-04-19",
      "customer_name": "Luc\u00eda Fern\u00e1ndez",
      "customer_email": "lucia.fernandez@example.com",
      "sku": "SKU-105",
      "quantity": "1",
      "unit_price_usd": "71.20",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1046",
      "order_date": "2024-04-20",
      "customer_name": "Jonah Reyes",
      "customer_email": "jonah.reyes@example.com",
      "sku": "SKU-106",
      "quantity": "2",
      "unit_price_usd": "96.12",
      "status": "refunded",
      "region": "EU"
    },
    {
      "order_id": "ORD-1047",
      "order_date": "2024-04-21",
      "customer_name": "",
      "customer_email": "priya.nair@example.com",
      "sku": "SKU-107",
      "quantity": "3",
      "unit_price_usd": "1183.68",
      "status": "cancelled",
      "region": "EU"
    },
    {
      "order_id": "ORD-1048",
      "order_date": "2024-04-22",
      "customer_name": "Ole Bj\u00f8rnson",
      "customer_email": "ole.bjrnson@example.com",
      "sku": "SKU-108",
      "quantity": "4",
      "unit_price_usd": "156.83",
      "status": "paid",
      "region": "UK"
    },
    {
      "order_id": "ORD-1049",
      "order_date": "2024-04-23",
      "customer_name": "Hana Sato",
      "customer_email": "hana.sato@example.com",
      "sku": "SKU-101",
      "quantity": "5",
      "unit_price_usd": "29.99",
      "status": "pending",
      "region": "US"
    },
    {
      "order_id": "ORD-1050",
      "order_date": "2024-04-24",
      "customer_name": "Diego Mar\u00edn",
      "customer_email": "diego.marin@example.com",
      "sku": "SKU-102",
      "quantity": "1",
      "unit_price_usd": "23.81",
      "status": "refunded",
      "region": "EU"
    }
  ],
  "rejects": [
    {
      "source_row": "1",
      "order_id": "ORD-9003",
      "reason": "quantity must be >= 1"
    },
    {
      "source_row": "9",
      "order_id": "ORD-9007",
      "reason": "missing unit price on a paid order"
    },
    {
      "source_row": "10",
      "order_id": "ORD-9008",
      "reason": "invalid order date (2024-02-31)"
    },
    {
      "source_row": "22",
      "order_id": "ORD-9001",
      "reason": "quantity is not numeric"
    },
    {
      "source_row": "32",
      "order_id": "ORD-9004",
      "reason": "invalid email"
    },
    {
      "source_row": "42",
      "order_id": "ORD-9002",
      "reason": "quantity must be >= 1"
    },
    {
      "source_row": "45",
      "order_id": "ORD-9006",
      "reason": "SKU not in catalog"
    },
    {
      "source_row": "54",
      "order_id": "ORD-9005",
      "reason": "missing required email"
    }
  ]
}
RAW_SHA256 = "94619f864ba8c7e2ddf1bd4f0a1c50e352ca1412252295acf7376c2e20c700b3"

def _score_clean():
    try:
        expected_header = EXPECTED["clean_headers"]
        expected_rows = {r["order_id"]: r for r in EXPECTED["clean_rows"]}
        try:
            with open("clean/orders_clean.csv", encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
        except FileNotFoundError:
            return {"score": 0.0, "detail": "clean/orders_clean.csv not found"}
        if not rows:
            return {"score": 0.0, "detail": "clean/orders_clean.csv is empty"}
        header, data = rows[0], rows[1:]
        header_score = 1.0 if header == expected_header else (
            len(set(header) & set(expected_header)) / len(expected_header))
        count_score = max(0.0, 1.0 - abs(len(data) - len(expected_rows)) / len(expected_rows))
        oids = []
        for r in data:
            oids.append(r[0].strip() if r else "")
        sorted_score = 1.0 if oids == sorted(oids) and all(oids) else 0.0
        unique_score = 1.0 if len(set(oids)) == len(oids) and len(set(oids)) == len(expected_rows) else 0.0
        by_id = {}
        for r in data:
            if r:
                by_id.setdefault(r[0].strip(), r)
        total_fields = len(expected_rows) * len(expected_header)
        matched = 0
        for oid, exp in expected_rows.items():
            act = by_id.get(oid)
            if act is None or len(act) < len(expected_header):
                continue
            for idx, field in enumerate(expected_header):
                a, e = act[idx].strip(), exp[field]
                if field == "unit_price_usd":
                    try:
                        if abs(Decimal(a) - Decimal(e)) < Decimal("0.005"):
                            matched += 1
                    except InvalidOperation:
                        pass
                elif a == e:
                    matched += 1
        field_score = matched / total_fields if total_fields else 0.0
        try:
            with open("data/orders_export.csv", "rb") as f:
                source_intact = hashlib.sha256(f.read()).hexdigest() == RAW_SHA256
        except Exception:
            source_intact = False
        source_score = 1.0 if source_intact else 0.0
        score = (0.10 * header_score + 0.08 * count_score + 0.05 * sorted_score
                 + 0.05 * unique_score + 0.67 * field_score + 0.05 * source_score)
        detail = (f"header={header_score:.2f} rows={len(data)}/50 sorted={bool(sorted_score)} "
                  f"unique={bool(unique_score)} fields={matched}/{total_fields} "
                  f"source_intact={source_intact}")
        return {"score": min(1.0, score), "detail": detail}
    except Exception as exc:
        return {"score": 0.0, "detail": f"check crashed: {exc}"}

def _score_rejects():
    try:
        expected = EXPECTED["rejects"]
        try:
            with open("clean/rejects.csv", encoding="utf-8-sig", newline="") as f:
                reader = csv.reader(f)
                all_rows = list(reader)
        except FileNotFoundError:
            return {"score": 0.0, "detail": "clean/rejects.csv not found"}
        if not all_rows:
            return {"score": 0.0, "detail": "clean/rejects.csv is empty"}
        header = [h.strip().lower() for h in all_rows[0]]
        need = ["source_row", "order_id", "reason"]
        schema_score = 1.0 if header == need else (
            len(set(header) & set(need)) / len(need))
        idx = {k: (header.index(k) if k in header else None) for k in need}
        data = all_rows[1:]
        by_src, by_oid = {}, {}
        for r in data:
            if idx["source_row"] is not None and len(r) > idx["source_row"]:
                by_src[r[idx["source_row"]].strip()] = r
            if idx["order_id"] is not None and len(r) > idx["order_id"]:
                by_oid[r[idx["order_id"]].strip()] = r
        captured = 0
        for e in expected:
            r = by_src.get(e["source_row"]) or by_oid.get(e["order_id"])
            if r is None:
                continue
            if e["order_id"].strip() not in ",".join(r):
                continue
            if idx["reason"] is not None and len(r) > idx["reason"] and r[idx["reason"]].strip():
                captured += 1
        capture_score = captured / len(expected)
        score = 0.25 * schema_score + 0.75 * capture_score
        return {"score": min(1.0, score),
                "detail": f"schema={schema_score:.2f} captured={captured}/{len(expected)} total_rows={len(data)}"}
    except Exception as exc:
        return {"score": 0.0, "detail": f"check crashed: {exc}"}

def main():
    items = []
    weights = {"clean_csv_correctness": 0.40, "rejects_csv_correctness": 0.15}
    for rid, fn in (("clean_csv_correctness", _score_clean), ("rejects_csv_correctness", _score_rejects)):
        res = fn()
        items.append({"id": rid, "weight": weights[rid],
                      "score": round(res["score"], 4), "detail": res["detail"]})
    per_item = {i["id"]: i["score"] for i in items}
    wsum = sum(weights.values())
    total = sum(i["weight"] * i["score"] for i in items) / wsum if wsum else 1.0
    print(json.dumps({"per_item": per_item, "checks": items, "score": round(total, 4)}))

if __name__ == "__main__":
    main()
