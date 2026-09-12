# -*- coding: utf-8 -*-
"""
Unit Tests for Proportional Control Volatility Targeting
========================================================
Validates:
1. Exact backward compatibility of default and open-loop mode.
2. Significant reduction in multiplier churn and whipsaws under proportional control.
3. Substantial reduction in punitive OTC redemption fees.
4. Strict enforcement of [min_weight, max_weight] boundaries.
5. Strict T-1 information lag (zero lookahead bias).
"""

import os
import pytest
import numpy as np
import pandas as pd

from scripts.otc_fund.vol_target import run_vol_target_simulation, calc_rolling_portfolio_vol
from scripts.otc_fund.cashflows import build_cashflow_schedule

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="module")
def panel_data():
    panel_path = os.path.join(REPO_ROOT, "data", "otc_fund", "fund_dca_daily_panel_2015_2026.csv")
    assert os.path.exists(panel_path), f"Panel missing: {panel_path}"
    df = pd.read_csv(panel_path, index_col=0, parse_dates=True)
    return df

@pytest.fixture(scope="module")
def sample_setup(panel_data):
    trading_dates = panel_data.index
    schedule = build_cashflow_schedule(trading_dates, initial_lump=500000.0, dca_amount=5000.0, dca_freq="monthly")
    weights = {
        "bond_pure_000015": 0.40,
        "dividend_100032": 0.20,
        "gold_000216": 0.15,
        "nasdaq_000834": 0.15,
        "csi300_fund_050002": 0.10
    }
    return trading_dates, panel_data, schedule, weights

def test_open_loop_backward_compatibility(sample_setup):
    """Verify that default mode and explicit mode='open_loop' are identical."""
    trading_dates, nav_df, schedule, weights = sample_setup
    
    ledger_def, df_def = run_vol_target_simulation(
        trading_dates, nav_df, schedule, weights, target_vol=0.07, vol_window=60
    )
    ledger_ol, df_ol = run_vol_target_simulation(
        trading_dates, nav_df, schedule, weights, target_vol=0.07, vol_window=60, mode="open_loop"
    )
    
    np.testing.assert_allclose(df_def["total_asset"].values, df_ol["total_asset"].values, rtol=1e-10)
    np.testing.assert_allclose(df_def["risk_multiplier"].values, df_ol["risk_multiplier"].values, rtol=1e-10)
    assert ledger_def.total_fees_paid == pytest.approx(ledger_ol.total_fees_paid, rel=1e-6)

def test_proportional_control_reduces_churn_and_fees(sample_setup):
    """Verify that proportional control reduces multiplier churn and redemption fee friction."""
    trading_dates, nav_df, schedule, weights = sample_setup
    
    ledger_ol, df_ol, diag_ol = run_vol_target_simulation(
        trading_dates, nav_df, schedule, weights, target_vol=0.07, vol_window=60,
        mode="open_loop", return_diagnostics=True
    )
    
    ledger_pc, df_pc, diag_pc = run_vol_target_simulation(
        trading_dates, nav_df, schedule, weights, target_vol=0.07, vol_window=60,
        mode="proportional_control", kp=0.25, return_diagnostics=True
    )
    
    churn_ol = diag_ol["multiplier_churn"]
    churn_pc = diag_pc["multiplier_churn"]
    assert churn_pc < churn_ol * 0.60, f"Expected >40% churn reduction: pc={churn_pc:.2f} vs ol={churn_ol:.2f}"
    
    red_fees_ol = ledger_ol.total_red_fees_paid
    red_fees_pc = ledger_pc.total_red_fees_paid
    assert red_fees_pc < red_fees_ol, f"Expected redemption fee reduction: pc={red_fees_pc:.2f} vs ol={red_fees_ol:.2f}"

def test_proportional_control_bounds(sample_setup):
    """Verify that multiplier strictly respects [min_weight, max_weight]."""
    trading_dates, nav_df, schedule, weights = sample_setup
    min_w, max_w = 0.35, 0.95
    
    ledger_pc, df_pc = run_vol_target_simulation(
        trading_dates, nav_df, schedule, weights, target_vol=0.07, vol_window=60,
        min_weight=min_w, max_weight=max_w, mode="proportional_control", kp=0.25
    )
    
    mults = df_pc["risk_multiplier"].values
    assert np.all(mults >= min_w - 1e-9), f"Multiplier breached min_weight: {mults.min()}"
    assert np.all(mults <= max_w + 1e-9), f"Multiplier breached max_weight: {mults.max()}"

def test_vol_target_strict_t_minus_1_lag(panel_data):
    """Verify that rolling volatility at date t strictly shifts by 1 day (T-1 info only)."""
    weights = {"bond_pure_000015": 0.5, "dividend_100032": 0.5}
    rets = panel_data.pct_change()
    rolling_vols = calc_rolling_portfolio_vol(rets, weights, window=60)
    
    # First 60 elements must be NaN due to 60-day window + 1-day lag
    assert np.isnan(rolling_vols.iloc[0])
    assert np.isnan(rolling_vols.iloc[59])
    assert np.isnan(rolling_vols.iloc[60])  # Day 60 is NaN because of shift(1)
    assert np.isfinite(rolling_vols.iloc[61]) # First valid estimate is day 61
