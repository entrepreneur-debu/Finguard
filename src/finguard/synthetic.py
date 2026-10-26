"""Synthetic customers, merchants and transactions with hidden fraud patterns.

Fraud patterns injected (fraud_type values):
- account_takeover: new device + foreign IP + amount far above the customer's normal
- structuring: several transfers just under the $10,000 reporting threshold within 48 h
- card_testing: a burst of tiny online payments, then one big purchase
"""

import math
import random
import sqlite3
from datetime import UTC, datetime, timedelta

# Fixed "today" so the same seed always produces exactly the same data.
END = datetime(2026, 10, 1, tzinfo=UTC)
HISTORY_DAYS = 90
REPORTING_THRESHOLD = 10_000

COUNTRIES = ["IN", "US", "GB", "DE", "SG", "AE", "BR", "NG"]
FIRST_NAMES = ["Aarav", "Priya", "James", "Emma", "Lukas", "Mia", "Wei", "Aisha", "Carlos", "Zara"]
LAST_NAMES = ["Sharma", "Patel", "Smith", "Brown", "Muller", "Tan", "Khan", "Silva", "Okafor"]

# category -> high_risk (easy places to turn stolen money into cash)
MERCHANT_CATEGORIES = {
    "grocery": 0,
    "restaurant": 0,
    "fuel": 0,
    "travel": 0,
    "online_retail": 0,
    "electronics": 1,
    "gift_cards": 1,
    "crypto_exchange": 1,
}


def make_customers(rng: random.Random, n: int) -> list[dict]:
    customers = []
    for i in range(1, n + 1):
        signup = END - timedelta(days=rng.randint(180, 5 * 365))
        customers.append(
            {
                "customer_id": f"C{i:04d}",
                "name": f"{rng.choice(FIRST_NAMES)} {rng.choice(LAST_NAMES)}",
                "country": rng.choice(COUNTRIES),
                "signup_date": signup.date().isoformat(),
                # Median about $55, with a long tail of big spenders.
                "avg_spend": round(rng.lognormvariate(4.0, 0.8), 2),
                "risk_rating": rng.choices(["low", "medium", "high"], weights=[80, 15, 5])[0],
            }
        )
    return customers


def make_merchants(rng: random.Random, n: int) -> list[dict]:
    categories = list(MERCHANT_CATEGORIES)
    merchants = []
    for i in range(1, n + 1):
        category = categories[(i - 1) % len(categories)]  # every category is represented
        merchants.append(
            {
                "merchant_id": f"M{i:03d}",
                "name": f"{category.replace('_', ' ').title()} #{i}",
                "category": category,
                "country": rng.choice(COUNTRIES),
                "high_risk": MERCHANT_CATEGORIES[category],
            }
        )
    return merchants


def _txn(customer, ts, amount, channel, device, ip_country, merchant=None, counterparty=None,
         fraud_type=None) -> dict:
    return {
        "customer_id": customer["customer_id"],
        "merchant_id": merchant["merchant_id"] if merchant else None,
        "counterparty": counterparty,
        "amount": round(amount, 2),
        "timestamp": ts.isoformat(timespec="seconds"),
        "channel": channel,
        "device_id": device,
        "ip_country": ip_country,
        "is_fraud": 1 if fraud_type else 0,
        "fraud_type": fraud_type,
    }


def _devices(customer) -> list[str]:
    return [f"D-{customer['customer_id']}-1", f"D-{customer['customer_id']}-2"]


def _account(rng: random.Random) -> str:
    return f"ACC-{rng.randint(10_000_000, 99_999_999)}"


def _foreign_country(rng: random.Random, home: str) -> str:
    return rng.choice([c for c in COUNTRIES if c != home])


def make_normal_txns(rng: random.Random, customers, merchants) -> list[dict]:
    low_risk = [m for m in merchants if not m["high_risk"]]
    txns = []
    for c in customers:
        devices = _devices(c)
        for _ in range(rng.randint(10, 40)):
            ts = END - timedelta(seconds=rng.uniform(0, HISTORY_DAYS * 86_400))
            # Log-normal around the customer's own normal: always positive, right-skewed.
            amount = rng.lognormvariate(math.log(c["avg_spend"]), 0.5)
            channel = rng.choices(["card_present", "online", "transfer"], weights=[50, 35, 15])[0]
            device = rng.choice(devices)
            if channel == "transfer":
                txns.append(_txn(c, ts, amount, channel, device, c["country"],
                                 counterparty=_account(rng)))
            else:
                # Mostly everyday merchants, occasionally a high-risk one (legit customers buy
                # electronics too, so high_risk alone must not mean fraud).
                merchant = rng.choice(merchants if rng.random() < 0.1 else low_risk)
                txns.append(_txn(c, ts, amount, channel, device, c["country"], merchant=merchant))
    return txns


def _burst_start(rng: random.Random) -> datetime:
    return END - timedelta(days=rng.uniform(3, HISTORY_DAYS - 3))


def inject_account_takeover(rng: random.Random, victims, merchants) -> list[dict]:
    high_risk = [m for m in merchants if m["high_risk"]]
    txns = []
    for c in victims:
        start = _burst_start(rng)
        device = f"D-NEW-{rng.randint(1000, 9999)}"
        ip = _foreign_country(rng, c["country"])
        for k in range(rng.randint(1, 3)):
            ts = start + timedelta(minutes=10 * k + rng.uniform(0, 10))
            amount = c["avg_spend"] * rng.uniform(5, 20)
            if rng.random() < 0.5:
                txns.append(_txn(c, ts, amount, "online", device, ip,
                                 merchant=rng.choice(high_risk), fraud_type="account_takeover"))
            else:
                txns.append(_txn(c, ts, amount, "transfer", device, ip,
                                 counterparty=_account(rng), fraud_type="account_takeover"))
    return txns


def inject_structuring(rng: random.Random, victims) -> list[dict]:
    txns = []
    for c in victims:
        start = _burst_start(rng)
        device = _devices(c)[0]  # the real account holder is doing it
        for _ in range(rng.randint(3, 6)):
            ts = start + timedelta(hours=rng.uniform(0, 48))
            amount = rng.uniform(REPORTING_THRESHOLD - 1_000, REPORTING_THRESHOLD - 100)
            txns.append(_txn(c, ts, amount, "transfer", device, c["country"],
                             counterparty=_account(rng), fraud_type="structuring"))
    return txns


def inject_card_testing(rng: random.Random, victims, merchants) -> list[dict]:
    online = [m for m in merchants if m["category"] in ("online_retail", "gift_cards")]
    high_risk = [m for m in merchants if m["high_risk"]]
    txns = []
    for c in victims:
        start = _burst_start(rng)
        device = f"D-NEW-{rng.randint(1000, 9999)}"
        ip = _foreign_country(rng, c["country"])
        n_tests = rng.randint(5, 15)
        for k in range(n_tests):
            ts = start + timedelta(seconds=30 * k + rng.uniform(0, 30))
            txns.append(_txn(c, ts, rng.uniform(0.5, 3), "online", device, ip,
                             merchant=rng.choice(online), fraud_type="card_testing"))
        ts = start + timedelta(seconds=30 * n_tests + rng.uniform(60, 3600))
        txns.append(_txn(c, ts, c["avg_spend"] * rng.uniform(8, 15), "online", device, ip,
                         merchant=rng.choice(high_risk), fraud_type="card_testing"))
    return txns


def generate(conn: sqlite3.Connection, seed: int = 42, n_customers: int = 200,
             n_merchants: int = 50) -> dict:
    """Fill an initialised database with synthetic data. Returns row counts."""
    rng = random.Random(seed)
    customers = make_customers(rng, n_customers)
    merchants = make_merchants(rng, n_merchants)

    # Each victim suffers only one fraud pattern.
    victims = rng.sample(customers, 35)
    txns = make_normal_txns(rng, customers, merchants)
    txns += inject_account_takeover(rng, victims[:25], merchants)
    txns += inject_structuring(rng, victims[25:30])
    txns += inject_card_testing(rng, victims[30:], merchants)

    txns.sort(key=lambda t: t["timestamp"])
    for i, t in enumerate(txns, start=1):
        t["txn_id"] = f"T{i:06d}"

    conn.executemany(
        "INSERT INTO customers VALUES (:customer_id, :name, :country, :signup_date, "
        ":avg_spend, :risk_rating)",
        customers,
    )
    conn.executemany(
        "INSERT INTO merchants VALUES (:merchant_id, :name, :category, :country, :high_risk)",
        merchants,
    )
    conn.executemany(
        "INSERT INTO transactions VALUES (:txn_id, :customer_id, :merchant_id, :counterparty, "
        ":amount, :timestamp, :channel, :device_id, :ip_country, :is_fraud, :fraud_type)",
        txns,
    )
    conn.commit()  # one commit for everything: far faster than committing per row

    return {
        "customers": len(customers),
        "merchants": len(merchants),
        "transactions": len(txns),
        "fraud": sum(t["is_fraud"] for t in txns),
    }
