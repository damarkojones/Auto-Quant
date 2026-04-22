"""
prepare.py — READ-ONLY. Part of the evaluation contract, do not modify.

One-time setup: check env + download BTC/USDT and ETH/USDT 1h OHLCV from Binance.

Usage:
    uv run prepare.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Env check — talib is hard to install on macOS ARM; give clear remediation.
# ---------------------------------------------------------------------------
try:
    import talib  # noqa: F401
except ImportError:
    print(
        "ERROR: TA-Lib is not installed.\n\n"
        "Two install paths (see README.md for full detail):\n"
        "  1. Native: `brew install ta-lib` then `uv sync`\n"
        "  2. Docker fallback: `docker compose run --rm freqtrade ...`\n",
        file=sys.stderr,
    )
    sys.exit(1)

from freqtrade.commands.data_commands import start_download_data  # noqa: E402

# ---------------------------------------------------------------------------
# Fixed constants — these define the evaluation arena. Do not modify.
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).parent.resolve()
USER_DATA = PROJECT_DIR / "user_data"
CONFIG = PROJECT_DIR / "config.json"

EXCHANGE = "binance"
PAIRS = ["BTC/USDT", "ETH/USDT"]
TIMEFRAMES = ["1h"]
TIMERANGE = "20230101-20251231"


def data_exists() -> bool:
    data_dir = USER_DATA / "data" / EXCHANGE
    for pair in PAIRS:
        filename = f"{pair.replace('/', '_')}-1h.feather"
        if not (data_dir / filename).exists():
            return False
    return True


def download() -> None:
    args = {
        "config": [str(CONFIG)],
        "user_data_dir": str(USER_DATA),
        "datadir": str(USER_DATA / "data"),
        "exchange": EXCHANGE,
        "pairs": PAIRS,
        "timeframes": TIMEFRAMES,
        "timerange": TIMERANGE,
        "dataformat_ohlcv": "feather",
        "dataformat_trades": "feather",
        "download_trades": False,
        "trading_mode": "spot",
        "prepend_data": False,
        "erase": False,
        "include_inactive_pairs": False,
        "new_pairs_days": 30,
    }
    start_download_data(args)


def main() -> None:
    if data_exists():
        print(f"Data already present at {USER_DATA / 'data' / EXCHANGE}")
        print("Ready.")
        return

    print(f"Exchange:   {EXCHANGE}")
    print(f"Pairs:      {PAIRS}")
    print(f"Timeframes: {TIMEFRAMES}")
    print(f"Timerange:  {TIMERANGE}")
    print(f"Dest:       {USER_DATA / 'data' / EXCHANGE}")
    print()

    download()

    if not data_exists():
        print(
            "ERROR: download appeared to succeed but expected files are missing.\n"
            f"Check {USER_DATA / 'data' / EXCHANGE}/",
            file=sys.stderr,
        )
        sys.exit(1)

    print()
    print("Ready.")


if __name__ == "__main__":
    main()
