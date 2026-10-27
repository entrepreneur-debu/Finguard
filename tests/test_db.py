import sqlite3

import pytest

from finguard.db import connect, init_schema


def test_tables_created(tmp_path):
    conn = connect(tmp_path / "test.db")
    init_schema(conn)
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert tables == {"customers", "merchants", "transactions"}


def test_init_schema_twice(tmp_path):
    conn = connect(tmp_path / "test.db")
    init_schema(conn)
    init_schema(conn)  # must not raise


def test_foreign_key_enforced(tmp_path):
    conn = connect(tmp_path / "test.db")
    init_schema(conn)
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute(
            "INSERT INTO transactions (txn_id, customer_id, amount, timestamp, channel, "
            "device_id, ip_country, is_fraud) "
            "VALUES ('T1', 'NO-SUCH-CUSTOMER', 10.0, '2026-06-01T10:00:00+00:00', 'online', "
            "'D1', 'IN', 0)"
        )
