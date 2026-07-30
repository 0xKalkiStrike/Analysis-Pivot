"""Generate synthetic Excel/CSV datasets with intentional duplicates,
conflicts and validation errors — useful for demo & testing."""
from __future__ import annotations

import random
import sys
from pathlib import Path

import polars as pl
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)


def _customers(n: int = 500, dup_ratio: float = 0.08) -> pl.DataFrame:
    rows: list[dict] = []
    for i in range(n):
        rows.append({
            "customer_id": f"C{i:05d}",
            "name": fake.name(),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "company": fake.company(),
            "gst": f"{random.randint(10, 37):02d}{fake.lexify('?????').upper()}"
                   f"{random.randint(1000, 9999)}{fake.random_letter().upper()}"
                   f"1Z{random.choice('ABCDEF1234567890')}",
            "city": fake.city(),
            "state": fake.state(),
            "country": "India" if random.random() < 0.7 else fake.country(),
            "zip": fake.postcode(),
            "amount": round(random.uniform(100, 100_000), 2),
            "created": fake.date_between(start_date="-2y").isoformat(),
        })

    # Introduce duplicates + typos + case changes + extra whitespace
    dup_count = int(n * dup_ratio)
    for _ in range(dup_count):
        base = random.choice(rows)
        modified = dict(base)
        style = random.choice(["case", "space", "typo", "email_case"])
        if style == "case":
            modified["name"] = modified["name"].upper()
        elif style == "space":
            modified["name"] = f"  {modified['name']}  "
            modified["city"] = f"{modified['city']} "
        elif style == "typo":
            n_ = modified["name"]
            if len(n_) > 3:
                pos = random.randint(1, len(n_) - 2)
                modified["name"] = n_[:pos] + n_[pos + 1] + n_[pos] + n_[pos + 2:]
        elif style == "email_case":
            modified["email"] = modified["email"].upper()
        rows.append(modified)

    # Introduce some invalid rows
    for i in range(int(n * 0.02)):
        rows.append({
            "customer_id": f"BAD{i}", "name": "", "email": "not-an-email",
            "phone": "abc", "company": None, "gst": "INVALID",
            "city": None, "state": "", "country": "??",
            "zip": "xx", "amount": -50, "created": "not-a-date",
        })

    random.shuffle(rows)
    return pl.DataFrame(rows)


def _invoices(customers: pl.DataFrame, n: int = 800) -> pl.DataFrame:
    ids = customers["customer_id"].to_list()
    rows = []
    for i in range(n):
        cid = random.choice(ids)
        rows.append({
            "invoice_no": f"INV-{2024}-{i:05d}",
            "customer_id": cid,
            "product": fake.word().title(),
            "quantity": random.randint(1, 20),
            "unit_price": round(random.uniform(50, 5000), 2),
            "total": None,  # will compute
            "date": fake.date_between(start_date="-1y").isoformat(),
            "status": random.choice(["paid", "pending", "overdue", "cancelled"]),
        })
    df = pl.DataFrame(rows)
    df = df.with_columns((pl.col("quantity") * pl.col("unit_price")).alias("total"))
    return df


def _products(n: int = 120) -> pl.DataFrame:
    rows = []
    for i in range(n):
        rows.append({
            "sku": f"SKU-{i:04d}",
            "product_name": fake.catch_phrase(),
            "category": random.choice(["Electronics", "Apparel", "Home", "Books", "Toys", "Grocery"]),
            "price": round(random.uniform(10, 5000), 2),
            "stock": random.randint(0, 500),
            "supplier": fake.company(),
        })
    # Introduce fuzzy-duplicate product names
    for i in range(8):
        p = random.choice(rows)
        rows.append({**p, "sku": f"SKU-D{i:04d}", "product_name": p["product_name"].lower()})
    return pl.DataFrame(rows)


def generate(out_dir: str | Path = "samples") -> list[str]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    files: list[str] = []

    customers = _customers()
    invoices = _invoices(customers)
    products = _products()

    # Split customers into two overlapping files (for merge testing)
    half = customers.height // 2
    part_a = customers.head(half + 30)
    part_b = customers.tail(customers.height - half + 30)

    tasks = [
        ("customers_region_a.xlsx", part_a),
        ("customers_region_b.xlsx", part_b),
        ("invoices_2024.xlsx", invoices),
        ("products_catalog.xlsx", products),
        ("customers.csv", customers),
    ]
    for name, df in tasks:
        p = out / name
        if name.endswith(".csv"):
            df.write_csv(p)
        else:
            df.write_excel(p)
        files.append(str(p))
        print(f"wrote {p}  ({df.height} rows, {df.width} cols)")
    return files


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "samples"
    generate(target)
