"""
run.py — READ-ONLY. The oracle. Do not modify.

Runs a single backtest on the current AutoResearch strategy via FreqTrade's
Python API (not CLI), then prints a parseable --- summary block to stdout.

Usage:
    uv run run.py > run.log 2>&1
    grep "^sharpe:\\|^trade_count:\\|^max_drawdown_pct:" run.log
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any

from freqtrade.configuration import Configuration
from freqtrade.enums import RunMode
from freqtrade.optimize.backtesting import Backtesting

# ---------------------------------------------------------------------------
# Fixed constants. Do not modify.
# ---------------------------------------------------------------------------
PROJECT_DIR = Path(__file__).parent.resolve()
USER_DATA = PROJECT_DIR / "user_data"
CONFIG = PROJECT_DIR / "config.json"
STRATEGY_NAME = "AutoResearch"
TIMERANGE = "20230101-20251231"
PAIRS_STR = "BTC/USDT,ETH/USDT"


def get_commit() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(PROJECT_DIR),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "unknown"


def run_backtest() -> dict[str, Any]:
    args = {
        "config": [str(CONFIG)],
        "user_data_dir": str(USER_DATA),
        "datadir": str(USER_DATA / "data"),
        "strategy": STRATEGY_NAME,
        "strategy_path": str(USER_DATA / "strategies"),
        "timerange": TIMERANGE,
        "export": "none",
        "exportfilename": None,
        "cache": "none",
    }
    config = Configuration(args, RunMode.BACKTEST).get_config()
    bt = Backtesting(config)
    bt.start()
    return bt.results


def _get(d: dict[str, Any], *keys: str, default: float = 0.0) -> float:
    """Defensive extract — tries several key names, returns default if none match."""
    for k in keys:
        if k in d and d[k] is not None:
            try:
                return float(d[k])
            except (TypeError, ValueError):
                continue
    return default


def extract_metrics(results: dict[str, Any]) -> dict[str, float]:
    """
    Extract key metrics from FreqTrade backtest results.

    FreqTrade's result structure has evolved across versions; we try several
    likely key names defensively. If a metric is missing it's reported as 0.0.
    """
    strat = results.get("strategy", {}).get(STRATEGY_NAME, {}) or {}

    return {
        "sharpe": _get(strat, "sharpe", "sharpe_ratio"),
        "sortino": _get(strat, "sortino", "sortino_ratio"),
        "calmar": _get(strat, "calmar", "calmar_ratio"),
        "total_profit_pct": _get(strat, "profit_total_pct", "profit_total") * (
            1 if "profit_total_pct" in strat else 100
        ),
        "max_drawdown_pct": -abs(
            _get(strat, "max_drawdown_account", "max_drawdown", "max_drawdown_abs")
        )
        * (100 if "max_drawdown_account" in strat else 1),
        "trade_count": int(_get(strat, "total_trades", "trades")),
        "win_rate_pct": _get(strat, "winrate", "wins_rate") * 100,
        "profit_factor": _get(strat, "profit_factor"),
    }


def main() -> None:
    print(f"Running backtest: {STRATEGY_NAME} on {PAIRS_STR} 1h, timerange {TIMERANGE}")
    print()

    results = run_backtest()
    metrics = extract_metrics(results)
    commit = get_commit()

    print()
    print("---")
    print(f"strategy:         {STRATEGY_NAME}")
    print(f"commit:           {commit}")
    print(f"timerange:        {TIMERANGE}")
    print(f"sharpe:           {metrics['sharpe']:.4f}")
    print(f"sortino:          {metrics['sortino']:.4f}")
    print(f"calmar:           {metrics['calmar']:.4f}")
    print(f"total_profit_pct: {metrics['total_profit_pct']:.4f}")
    print(f"max_drawdown_pct: {metrics['max_drawdown_pct']:.4f}")
    print(f"trade_count:      {metrics['trade_count']}")
    print(f"win_rate_pct:     {metrics['win_rate_pct']:.4f}")
    print(f"profit_factor:    {metrics['profit_factor']:.4f}")
    print(f"pairs:            {PAIRS_STR}")


if __name__ == "__main__":
    main()
