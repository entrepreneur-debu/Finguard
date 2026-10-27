"""Create data/finguard.db filled with synthetic data.

Usage: python scripts/generate_data.py [--seed 42]
"""

import argparse

from finguard.config import DB_PATH
from finguard.db import connect, init_schema
from finguard.synthetic import generate


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    DB_PATH.unlink(missing_ok=True)  # start fresh so reruns don't hit duplicate IDs
    conn = connect(DB_PATH)
    init_schema(conn)
    counts = generate(conn, seed=args.seed)
    conn.close()

    rate = counts["fraud"] / counts["transactions"]
    print(f"Created {DB_PATH}")
    print(f"  customers:    {counts['customers']}")
    print(f"  merchants:    {counts['merchants']}")
    print(f"  transactions: {counts['transactions']}  (fraud: {counts['fraud']}, {rate:.1%})")


if __name__ == "__main__":
    main()
