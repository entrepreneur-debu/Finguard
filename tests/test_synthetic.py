from finguard.db import connect, init_schema
from finguard.synthetic import REPORTING_THRESHOLD, generate


def build(path, seed=42):
    conn = connect(path)
    init_schema(conn)
    generate(conn, seed=seed)
    return conn


def all_txns(conn):
    return [tuple(r) for r in conn.execute("SELECT * FROM transactions ORDER BY txn_id")]


def test_same_seed_gives_same_data(tmp_path):
    a = build(tmp_path / "a.db")
    b = build(tmp_path / "b.db")
    assert all_txns(a) == all_txns(b)


def test_different_seed_gives_different_data(tmp_path):
    a = build(tmp_path / "a.db", seed=1)
    b = build(tmp_path / "b.db", seed=2)
    assert all_txns(a) != all_txns(b)


def test_fraud_rate_and_types(tmp_path):
    conn = build(tmp_path / "test.db")
    total, fraud = conn.execute("SELECT COUNT(*), SUM(is_fraud) FROM transactions").fetchone()
    assert 0.01 <= fraud / total <= 0.05

    types = {r[0] for r in conn.execute("SELECT DISTINCT fraud_type FROM transactions WHERE is_fraud")}
    assert types == {"account_takeover", "structuring", "card_testing"}


def test_structuring_stays_under_threshold(tmp_path):
    conn = build(tmp_path / "test.db")
    (max_amount,) = conn.execute(
        "SELECT MAX(amount) FROM transactions WHERE fraud_type = 'structuring'"
    ).fetchone()
    assert max_amount < REPORTING_THRESHOLD
