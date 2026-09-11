# -*- coding: utf-8 -*-
"""
Multi-Asset Optimization Comparison (Remediated)
===============================================
Remediated to use strict chronological forward ledger.
Completely eliminates the future cash lookahead bug and removes all hardcoded D:\ paths.
"""

import os
import sys
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.cashflows import build_cashflow_schedule
from scripts.otc_fund.ledger import run_chronological_simulation
from scripts.otc_fund.metrics import evaluate_portfolio

PROXY_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "asset_class_proxy_panel_2015_2026.csv")

def run_comparison():
    if not os.path.exists(PROXY_CSV):
        raise FileNotFoundError(f"Data not found: {PROXY_CSV}")
    df = pd.read_csv(PROXY_CSV, index_col=0, parse_dates=True)
    dates = df.index
    
    cfs = build_cashflow_schedule(dates, initial_lump=1000000.0, dca_amount=10000.0, dca_freq="monthly")
    
    # 1. 9-Asset
    w9 = {
        "bond_pure_000015": 0.15, "proxy_bond_qdii": 0.10, "dividend_100032": 0.10,
        "money_market_000198": 0.10, "proxy_quant_a": 0.10, "gold_000216": 0.15,
        "nasdaq_000834": 0.15, "proxy_global_tech": 0.10, "proxy_oil": 0.05
    }
    _, df9 = run_chronological_simulation(dates, df, cfs, w9)
    m9 = evaluate_portfolio(df9["total_asset"], df9["cumulative_invested"], cfs)
    
    # 2. 7-Asset Modified
    w7 = {
        "bond_pure_000015": 0.25, "dividend_100032": 0.10, "money_market_000198": 0.10,
        "proxy_quant_a": 0.10, "gold_000216": 0.20, "nasdaq_000834": 0.15,
        "proxy_global_tech": 0.10
    }
    _, df7 = run_chronological_simulation(dates, df, cfs, w7)
    m7 = evaluate_portfolio(df7["total_asset"], df7["cumulative_invested"], cfs)
    
    print("Optimization Comparison Results:")
    print(f"9-Asset Plan: Ending={m9['ending_value']/10000:.2f}w, XIRR={m9['xirr']*100:.2f}%, Sharpe={m9['sharpe_ratio']:.2f}, MaxDD={m9['twr_max_drawdown']*100:.2f}%")
    print(f"7-Asset Plan: Ending={m7['ending_value']/10000:.2f}w, XIRR={m7['xirr']*100:.2f}%, Sharpe={m7['sharpe_ratio']:.2f}, MaxDD={m7['twr_max_drawdown']*100:.2f}%")

if __name__ == "__main__":
    run_comparison()
