"""SQLite database: schema and connection helpers for FinGuard."""

import sqlite3
from pathlib import Path

from finguard.config import DB_PATH

SCHEMA = """
Create table if not exists customers (
    customer_id text primary key,
    name text not null,
    country text not null,
    signup_date text not null,
    avg_spend real not null,
    risk_rating text not null
);
Create table if not exists merchants (
    merchant_id text primary key,
    name text not null,
    category text not null,
    country text not null,
    high_risk integer not null
);
Create table if not exists transactions (
    txn_id text primary key,
    customer_id text not null references customers(customer_id),
    merchant_id text references merchants(merchant_id),
    counterparty text,
    amount real not null,
    timestamp text not null,
    channel text not null,
    device_id text not null,
    ip_country text not null,
    is_fraud integer not null,
    fraud_type text
);
Create index if not exists transactions_customer_id_timestamp on transactions(customer_id, timestamp);
"""


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    """Open a connection to the SQLite database at `path`."""
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    # SQLite ignores REFERENCES constraints unless this is turned on per connection.
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes (safe to run more than once)."""
    conn.executescript(SCHEMA)
