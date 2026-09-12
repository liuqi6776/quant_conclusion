# -*- coding: utf-8 -*-
"""
Unit Tests for QDII FX Exposure Modeling & Return Attribution Engine
====================================================================
Validates:
1. Exact mathematical identity: R_cny = R_usd + R_fx + R_usd * R_fx.
2. Exact log-CAGR additive identity: ln(1 + g_cny) = ln(1 + g_usd) + ln(1 + g_fx).
3. Data integrity of the official SAFE USD/CNY exchange rate series.
4. Annual attribution consistency with total period cumulative return.
5. Currency reversal stress testing behavior.
"""

import os
import pytest
import numpy as np
import pandas as pd

from scripts.otc_fund.fx_attribution import (
    load_fx_series,
    decompose_qdii_return,
    compute_yearly_attribution_table,
    simulate_fx_reversal_stress
)

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope="module")
def fx_and_panel():
    fx = load_fx_series()
    panel_path = os.path.join(REPO_ROOT, "data", "otc_fund", "fund_dca_daily_panel_2015_2026.csv")
    panel = pd.read_csv(panel_path, index_col=0, parse_dates=True)
    return fx, panel

def test_fx_series_data_integrity(fx_and_panel):
    """Verify SAFE USD/CNY series has zero nulls and strictly realistic bounds."""
    fx, panel = fx_and_panel
    assert len(fx) == len(panel), f"Length mismatch: fx={len(fx)} vs panel={len(panel)}"
    assert fx.isnull().sum() == 0, "USD/CNY series contains NaN values"
    assert (fx > 5.5).all() and (fx < 8.5).all(), "USD/CNY contains out-of-bounds rates"
    assert fx.index[0] == pd.Timestamp("2015-01-05")
    assert fx.index[-1] == pd.Timestamp("2026-08-06")

def test_exact_3way_return_identity(fx_and_panel):
    """Verify R_cny = R_usd + R_fx + R_usd * R_fx to 1e-10 numerical precision."""
    fx, panel = fx_and_panel
    res = decompose_qdii_return(panel["nasdaq_000834"], fx)
    
    r_cny = res["return_cny"]
    r_usd = res["return_usd"]
    r_fx = res["return_fx"]
    inter = res["interaction"]
    
    reconstructed = r_usd + r_fx + inter
    assert abs(reconstructed - r_cny) < 1e-10, f"Identity violated: {reconstructed} vs {r_cny}"
    assert res["identity_reconciled"] is True

def test_log_cagr_additive_identity(fx_and_panel):
    """Verify ln(1 + g_cny) = ln(1 + g_usd) + ln(1 + g_fx) to 1e-10 precision."""
    fx, panel = fx_and_panel
    res = decompose_qdii_return(panel["nasdaq_000834"], fx)
    
    g_cny = res["cagr_cny"]
    g_usd = res["cagr_usd"]
    g_fx = res["cagr_fx"]
    
    lhs = np.log(1.0 + g_cny)
    rhs = np.log(1.0 + g_usd) + np.log(1.0 + g_fx)
    assert abs(lhs - rhs) < 1e-10, f"Log-CAGR additivity violated: lhs={lhs} vs rhs={rhs}"
    
    # Verify shares sum to 1.0
    total_share = res["log_additive_share_usd"] + res["log_additive_share_fx"]
    assert abs(total_share - 1.0) < 1e-10

def test_yearly_attribution_compounding(fx_and_panel):
    """Verify annual compounded returns match full period cumulative return."""
    fx, panel = fx_and_panel
    df_y = compute_yearly_attribution_table(panel["nasdaq_000834"], fx)
    
    assert len(df_y) >= 12  # 2015 to 2026
    compounded_cny = (1.0 + df_y["cny_return"]).prod() - 1.0
    res = decompose_qdii_return(panel["nasdaq_000834"], fx)
    assert abs(compounded_cny - res["return_cny"]) < 1e-6

def test_fx_reversal_stress_monotonicity():
    """Verify stress test shows increasing drawdown as RMB appreciates."""
    df_stress = simulate_fx_reversal_stress(6.3237, fx_shocks=[-0.05, -0.10, -0.15])
    assert len(df_stress) == 3
    assert (df_stress["stressed_nav"] < 6.3237).all()
    # Decreasing monotonic
    assert (df_stress["stressed_nav"].diff().dropna() < 0).all()
