# Auto-Quant

> LLM-native autonomous quant research loop. Karpathy's [autoresearch](https://github.com/karpathy/autoresearch)
> pattern applied to FreqTrade strategies on BTC/USDT + ETH/USDT @ 1h.

The idea: give an LLM agent a FreqTrade backtest harness and a single strategy
file. The agent modifies the strategy, runs a backtest, checks if the result
improved, keeps or discards, and repeats. Over many iterations the hope is to
observe which patterns the LLM actually finds useful on this asset pair. The
**loop is in `program.md`** — not in any orchestrator — and is executed by
whatever LLM agent you point at the repo.

This is a prototype to validate whether Karpathy's autoresearch pattern
transfers to quant research. The metric is "did the loop run and produce
interpretable `results.tsv`", not "did we find a profitable strategy".

## How it works

Four files that matter:

- **`config.json`** — FreqTrade config, fixed. Pairs, timeframe, fees, dry-run
  wallet, timerange. The agent does not touch this.
- **`prepare.py`** — one-time data download from Binance via FreqTrade's Python
  API. The agent does not touch this.
- **`run.py`** — in-process backtest. Calls FreqTrade's `Backtesting` class
  directly (no CLI), extracts key metrics, prints a parseable `---` summary
  block to stdout. The agent does not touch this.
- **`user_data/strategies/AutoResearch.py`** — **the only file the agent edits**.
  Contains the full strategy: indicators, entry/exit logic, ROI/stoploss. This
  is the `train.py` equivalent of Karpathy's setup.

Plus:

- **`program.md`** — the autonomous-research instructions the human points the
  LLM agent at. This is the analog of Karpathy's `program.md`.
- **`results.tsv`** — the journal. `commit | sharpe | max_dd | status | description`.
  Git-ignored so it survives `git reset --hard` when the agent rolls back a
  failed experiment.
- **`analysis.ipynb`** — post-hoc read of `results.tsv`. Run after the loop has
  collected some data.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) for package management
- TA-Lib (the C library) — this is the annoying part on macOS

## Install

### Path 1 — native (preferred)

```bash
# 1. Install uv if you don't have it
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Install TA-Lib C library (macOS)
brew install ta-lib

# (Linux: follow https://github.com/mrjbq7/ta-lib#dependencies)

# 3. Install Python deps
uv sync

# 4. One-time data download (~a few minutes)
uv run prepare.py

# 5. Sanity check — run the baseline backtest
uv run run.py > run.log 2>&1 && grep "^---" -A 11 run.log
```

If step 5 prints a `---` block with a `sharpe:` line, you're ready.

### Path 2 — Docker fallback

If native TA-Lib install fails (common on some macOS ARM setups), use the
FreqTrade Docker image as the runtime. In that mode you still run `prepare.py`
and `run.py` as-is, but wrapped via Docker. TODO: add a `docker-compose.yml`.
For now, if you hit this, file an issue or escape-hatch by installing FreqTrade
in a conda env with `conda install -c conda-forge ta-lib`.

## Running the agent

Open a **second** terminal (not the one where you're editing files), `cd` into
this repo, and start your agent of choice with permissions disabled:

```bash
cd /Users/ame/2605dev/Auto-Quant
claude --dangerously-skip-permissions
```

Then prompt:

> Hi, have a look at `program.md` and let's kick off a new experiment.
> Let's do the setup first.

The agent reads `program.md`, goes through the setup steps, then enters the
experiment loop. It will keep iterating until you interrupt it (Ctrl-C) or it
runs out of context.

## Project structure

```
Auto-Quant/
├── README.md                          # you are here
├── pyproject.toml                     # uv-managed deps
├── .python-version                    # 3.11
├── config.json                        # FreqTrade config (READ-ONLY)
├── prepare.py                         # data download (READ-ONLY)
├── run.py                             # backtest + summary (READ-ONLY)
├── program.md                         # agent instructions
├── analysis.ipynb                     # post-hoc analysis
├── user_data/
│   ├── strategies/
│   │   └── AutoResearch.py            # THE one file the agent edits
│   ├── data/                          # gitignored — downloaded OHLCV
│   └── backtest_results/              # gitignored — FreqTrade outputs
└── results.tsv                        # gitignored — agent's journal
```

## Design notes

- **Agent only modifies one file.** All other files are evaluation contract.
  This is the single biggest design decision; it keeps diffs reviewable and
  prevents Goodharting the metric.
- **No CLI.** The agent only runs `uv run prepare.py` and `uv run run.py`.
  `run.py` uses FreqTrade's `Backtesting` class in-process, so startup is fast
  and errors are real Python stack traces.
- **`results.tsv` is gitignored.** When the agent reverts a failed experiment
  with `git reset --hard`, the journal of what was tried survives. This is
  essential to avoid re-trying the same bad ideas.
- **LLM decides keep/discard, not a scalar rule.** Backtest Sharpe on a finite
  window is noisy. Rather than `if new_sharpe > old_sharpe: keep`, the agent
  reads the full summary block and decides based on sharpe + drawdown + trade
  count + its own read on the asset.

## License

MIT (or whatever you prefer — this is a prototype).
