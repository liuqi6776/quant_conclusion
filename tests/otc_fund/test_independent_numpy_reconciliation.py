# -*- coding: utf-8 -*-
"""
Independent Standalone Numpy Reconciliation Test
================================================
Verifies that ledger.py execution for Scenario B (Pure Monthly DCA with Dividends)
matches an independent, self-contained raw numpy/pandas reconciliation
down to the penny.
"""
import os
import sys
import yaml
import pytest
import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.instruments import resolve_sub_fee
from scripts.otc_fund.cashflows import build_cashflow_schedule
from scripts.otc_fund.ledger import run_chronological_simulation

PROXY_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "asset_class_proxy_panel_2015_2026.csv")
DIV_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "dividend_events.csv")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "otc_fund", "fund_dca.yaml")


def test_independent_numpy_reconciliation_scenario_b():
    """Verify Scenario B ending value against a raw, non-ledger mathematical calculation."""
    assert os.path.exists(PROXY_CSV), f"Proxy panel missing: {PROXY_CSV}"
    assert os.path.exists(CONFIG_PATH), f"Config missing: {CONFIG_PATH}"

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    weights = cfg["portfolios"]["modified_7_asset"]["weights"]
    sub_fee_default = cfg["fee_model"]["subscription_fee_rate"]

    df = pd.read_csv(PROXY_CSV, index_col=0, parse_dates=True)
    dates = df.index
    cfs = build_cashflow_schedule(dates, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")
    div_df = pd.read_csv(DIV_CSV, parse_dates=["date"]) if os.path.exists(DIV_CSV) else None

    # 1. Independent Raw Numpy Computation
    deposit_dates = {dt: float(amt) for dt, amt in cfs.items() if amt > 0}
    div_by_date = {}
    if div_df is not None:
        for _, row in div_df.iterrows():
            div_by_date.setdefault(pd.Timestamp(row["date"]), []).append(row)

    shares = {col: 0.0 for col in weights.keys()}
    total_invested = 0.0

    for dt in dates:
        # Step 0: Dividend reinvestment (zero fee, before daily deposit)
        if dt in div_by_date:
            for d in div_by_date[dt]:
                col = d["target_column"]
                if col in shares and shares[col] > 0:
                    dps = float(d["dividend_per_share"])
                    px = float(df.loc[dt, col])
                    shares[col] += (shares[col] * dps) / px

        # Step 1: Monthly deposit allocation
        if dt in deposit_dates:
            amt = deposit_dates[dt]
            total_invested += amt
            for col, w in weights.items():
                alloc = amt * w
                fee = resolve_sub_fee(col, default_fee=sub_fee_default)
                net_inv = alloc / (1.0 + fee)
                nav = float(df.loc[dt, col])
                shares[col] += net_inv / nav

    # Final day valuation
    final_navs = {col: float(df.loc[dates[-1], col]) for col in weights.keys()}
    raw_final_mv = sum(shares[col] * final_navs[col] for col in weights.keys())

    # 2. Run Ledger Simulation
    _, df_res = run_chronological_simulation(dates, df, cfs, weights, sub_fee=sub_fee_default, dividend_events=div_df)
    ledger_final_mv = df_res["total_asset"].iloc[-1]
    ledger_invested = df_res["cumulative_invested"].iloc[-1]

    # 3. Assert Exact Reconciliation
    assert total_invested == 1400000.0, f"Expected 1400000.0 invested, got {total_invested}"
    assert ledger_invested == 1400000.0, f"Expected 1400000.0 invested, got {ledger_invested}"
    assert abs(raw_final_mv - ledger_final_mv) < 0.01, (
        f"Raw numpy MV {raw_final_mv:.2f} != Ledger MV {ledger_final_mv:.2f}"
    )
