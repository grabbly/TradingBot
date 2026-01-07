import os
import psycopg2
import matplotlib.pyplot as plt
from datetime import datetime, timedelta


def get_db_conn():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "***REMOVED***"),
        port=int(os.environ.get("PGPORT", "5432")),
        dbname=os.environ.get("PGDATABASE", "trading_bot"),
        user=os.environ.get("PGUSER", "n8n_user"),
        password=os.environ.get("PGPASSWORD", "***REMOVED***"),
    )


def fetch_ema_snapshots(symbol: str, days: int = 7):
    conn = get_db_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT timestamp, close_price, ema5, ema20
                FROM ema_snapshots
                WHERE symbol = %s
                  AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp
                """,
                (symbol, days),
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    timestamps = [r[0] for r in rows]
    close_prices = [float(r[1]) for r in rows]
    ema5 = [float(r[2]) if r[2] is not None else None for r in rows]
    ema20 = [float(r[3]) if r[3] is not None else None for r in rows]
    return timestamps, close_prices, ema5, ema20


def plot_ema(symbol: str = "NVDA", days: int = 7, output: str | None = None):
    ts, price, ema5, ema20 = fetch_ema_snapshots(symbol, days)
    if not ts:
        print("No data to plot")
        return

    plt.figure(figsize=(12, 6))
    plt.plot(ts, price, label="Close", color="black")
    plt.plot(ts, ema5, label="EMA 5", color="blue")
    plt.plot(ts, ema20, label="EMA 20", color="red")

    plt.title(f"{symbol} price and EMA (last {days} days)")
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    if output:
        plt.savefig(output)
        print(f"Saved plot to {output}")
    else:
        plt.show()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Plot price + EMA from Postgres ema_snapshots")
    parser.add_argument("--symbol", default="NVDA")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--output", help="Path to save PNG instead of showing")
    args = parser.parse_args()

    plot_ema(args.symbol, args.days, args.output)
