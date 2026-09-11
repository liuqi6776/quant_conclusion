# -*- coding: utf-8 -*-
"""
Audit Script: 9-Asset Fund DCA Strategy (2015 - 2026) vs. Shanghai Index & CSI 300
=================================================================================
Purpose:
  Independent, 100% reproducible audit script for the 9-Asset Fund DCA (定投) Strategy.
  Uses the bundled open-source dataset in `data/otc_fund/fund_dca_daily_panel_2015_2026.csv`.
  No private database or API credentials required.

Usage:
  python scripts/otc_fund/audit_fund_dca_2015_2026.py
"""

import os
import sys
import numpy as np
import pandas as pd
from scipy.optimize import brentq

# Resolve directory paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
DATA_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "fund_dca_daily_panel_2015_2026.csv")
DATA_PARQUET = os.path.join(REPO_ROOT, "data", "otc_fund", "fund_dca_daily_panel_2015_2026.parquet")

WEIGHTS = {
    "bond_pure_000015": 0.15,
    "bond_qdii_004998": 0.10,
    "dividend_100032": 0.10,
    "money_market_000198": 0.10,
    "quant_a_001917": 0.10,
    "gold_000216": 0.15,
    "nasdaq_000834": 0.15,
    "global_tech_017730": 0.10,
    "oil_501018": 0.05
}

SUB_FEE = 0.0015  # 0.15% subscription fee

def load_data():
    if os.path.exists(DATA_PARQUET):
        df = pd.read_parquet(DATA_PARQUET)
    elif os.path.exists(DATA_CSV):
        df = pd.read_csv(DATA_CSV, index_col=0, parse_dates=True)
    else:
        raise FileNotFoundError(f"Audit data not found at {DATA_CSV} or {DATA_PARQUET}")
    df.index = pd.to_datetime(df.index)
    return df

def calc_xirr(cash_flows, dates):
    def xnpv(rate, cfs, dts):
        d0 = dts[0]
        return sum(cf / ((1.0 + rate) ** ((d - d0).days / 365.0)) for cf, d in zip(cfs, dts))
    try:
        return brentq(lambda r: xnpv(r, cash_flows, dates), -0.9, 5.0)
    except Exception:
        return np.nan

def calc_dca_dd(val_s, inv_s):
    profit_ratio = val_s / inv_s
    cummax = profit_ratio.cummax()
    dd = (profit_ratio - cummax) / cummax
    return float(dd.min())

def audit_dca(monthly_invest=10000.0):
    df = load_data()
    dates = df.index
    n_days = len(dates)
    n_years = (dates[-1] - dates[0]).days / 365.25
    
    # 1. Normalized series
    sh_nav = df["sh_index_000001"] / df["sh_index_000001"].iloc[0]
    csi_nav = df["csi300_index"] / df["csi300_index"].iloc[0]
    
    # Normalized asset NAVs
    asset_navs = {}
    for col in WEIGHTS:
        asset_navs[col] = df[col] / df[col].iloc[0]
        
    # Portfolio daily return & static NAV
    port_ret = pd.Series(0.0, index=dates)
    for col, w in WEIGHTS.items():
        port_ret += asset_navs[col].pct_change().fillna(0) * w
    port_nav = (1.0 + port_ret).cumprod()

    # 2. Monthly DCA Simulation
    dca_shares_9 = {col: 0.0 for col in WEIGHTS}
    dca_shares_sh = 0.0
    dca_shares_csi = 0.0
    
    total_invested = 0.0
    inv_series = pd.Series(0.0, index=dates)
    val_9_series = pd.Series(0.0, index=dates)
    val_sh_series = pd.Series(0.0, index=dates)
    val_csi_series = pd.Series(0.0, index=dates)
    
    cfs_9, cfs_sh, cfs_csi, cf_dates = [], [], [], []
    
    for i, d in enumerate(dates):
        # Trigger on month change (BMS)
        if i == 0 or d.month != dates[i-1].month:
            total_invested += monthly_invest
            cfs_9.append(-monthly_invest)
            cfs_sh.append(-monthly_invest)
            cfs_csi.append(-monthly_invest)
            cf_dates.append(d)
            
            # Invest in 9 assets
            for col, w in WEIGHTS.items():
                alloc = monthly_invest * w * (1.0 - SUB_FEE)
                dca_shares_9[col] += alloc / asset_navs[col].loc[d]
                
            # Invest in Benchmarks
            dca_shares_sh += (monthly_invest * (1.0 - SUB_FEE)) / sh_nav.loc[d]
            dca_shares_csi += (monthly_invest * (1.0 - SUB_FEE)) / csi_nav.loc[d]
            
        cur_val_9 = sum(dca_shares_9[col] * asset_navs[col].loc[d] for col in WEIGHTS)
        cur_val_sh = dca_shares_sh * sh_nav.loc[d]
        cur_val_csi = dca_shares_csi * csi_nav.loc[d]
        
        inv_series.iloc[i] = total_invested
        val_9_series.iloc[i] = cur_val_9
        val_sh_series.iloc[i] = cur_val_sh
        val_csi_series.iloc[i] = cur_val_csi
        
    final_d = dates[-1]
    cfs_9.append(val_9_series.iloc[-1])
    cfs_sh.append(val_sh_series.iloc[-1])
    cfs_csi.append(val_csi_series.iloc[-1])
    cf_dates.append(final_d)
    
    xirr_9 = calc_xirr(cfs_9, cf_dates)
    xirr_sh = calc_xirr(cfs_sh, cf_dates)
    xirr_csi = calc_xirr(cfs_csi, cf_dates)
    
    dd_9 = calc_dca_dd(val_9_series, inv_series)
    dd_sh = calc_dca_dd(val_sh_series, inv_series)
    dd_csi = calc_dca_dd(val_csi_series, inv_series)

    # Output Audit Summary Table
    print("\n" + "="*86)
    print(f"   9-Asset Fund DCA Independent Audit Report (2015-01 to 2026-08, {n_years:.1f} Years)")
    print("="*86)
    print(f"{'Metric':<25} | {'9-Asset Stable DCA':<18} | {'Shanghai Index DCA':<18} | {'CSI 300 DCA':<18}")
    print("-" * 86)
    print(f"{'Total Principal Invested':<25} | {total_invested/10000:15.1f} W | {total_invested/10000:15.1f} W | {total_invested/10000:15.1f} W")
    print(f"{'Ending Market Value':<25} | {val_9_series.iloc[-1]/10000:15.1f} W | {val_sh_series.iloc[-1]/10000:15.1f} W | {val_csi_series.iloc[-1]/10000:15.1f} W")
    print(f"{'Net Profit Amount':<25} | {(val_9_series.iloc[-1]-total_invested)/10000:15.1f} W | {(val_sh_series.iloc[-1]-total_invested)/10000:15.1f} W | {(val_csi_series.iloc[-1]-total_invested)/10000:15.1f} W")
    print(f"{'Cumulative ROI':<25} | {(val_9_series.iloc[-1]/total_invested - 1)*100:14.2f}% | {(val_sh_series.iloc[-1]/total_invested - 1)*100:14.2f}% | {(val_csi_series.iloc[-1]/total_invested - 1)*100:14.2f}%")
    print(f"{'Annualized XIRR':<25} | {xirr_9*100:14.2f}% | {xirr_sh*100:14.2f}% | {xirr_csi*100:14.2f}%")
    print(f"{'DCA Max Drawdown':<25} | {dd_9*100:14.2f}% | {dd_sh*100:14.2f}% | {dd_csi*100:14.2f}%")
    print("="*86)

    # Verification Assertions
    assert val_9_series.iloc[-1] > total_invested * 2.0, "Audit failed: Final value should exceed 2x principal"
    assert xirr_9 > 0.10, "Audit failed: XIRR should exceed 10%"
    assert dd_9 > -0.20, "Audit failed: DCA Max Drawdown should be within -20%"
    print("\n[PASS] All audit assertions passed successfully!")

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    audit_dca()
