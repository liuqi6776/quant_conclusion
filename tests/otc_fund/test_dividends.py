# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.ledger import ForwardLedger

def test_cash_dividend_continuity():
    """Verify total portfolio asset continuity under cash dividend."""
    ledger = ForwardLedger(cash=10000.0)
    d0 = pd.Timestamp("2021-01-04")
    d_div = pd.Timestamp("2021-01-05")
    
    # Day 0: Buy 10000 RMB at NAV 2.0 (fee 0.0 for pure test) -> 5000 shares, market value 10000
    ledger.buy("TEST_FUND", d0, unit_nav=2.0, amount=10000.0, sub_fee_rate=0.0)
    tot_before = ledger.cash + ledger.get_shares("TEST_FUND") * 2.0
    assert tot_before == 10000.0
    
    # Ex-dividend date: 0.20 RMB dividend per share. Ex-dividend NAV drops to 1.80
    ledger.process_dividend("TEST_FUND", d_div, unit_nav=1.80, dividend_per_share=0.20, mode="cash")
    
    # After cash dividend: shares remain 5000 * 1.80 = 9000; cash = 1000. Total asset = 10000.0
    tot_after = ledger.cash + ledger.get_shares("TEST_FUND") * 1.80
    assert pytest.approx(tot_after, rel=1e-5) == 10000.0
    assert pytest.approx(ledger.cash, rel=1e-5) == 1000.0

def test_reinvestment_dividend_continuity():
    """Verify total portfolio asset continuity under dividend reinvestment."""
    ledger = ForwardLedger(cash=10000.0)
    d0 = pd.Timestamp("2021-01-04")
    d_div = pd.Timestamp("2021-01-05")
    
    ledger.buy("TEST_FUND", d0, unit_nav=2.0, amount=10000.0, sub_fee_rate=0.0)
    
    # 0.20 dividend per share. Payout = 5000 * 0.20 = 1000. Reinvested at ex-div NAV 1.80 -> 1000 / 1.80 = 555.555 shares
    ledger.process_dividend("TEST_FUND", d_div, unit_nav=1.80, dividend_per_share=0.20, mode="reinvest")
    
    # New total shares = 5000 + 555.555 = 5555.555. At NAV 1.80 -> 10000.0
    tot_after = ledger.cash + ledger.get_shares("TEST_FUND") * 1.80
    assert pytest.approx(tot_after, rel=1e-5) == 10000.0
    assert ledger.cash == 0.0

def test_simulation_with_real_dividends():
    """Verify that chronological simulation actually processes real fund dividends."""
    from scripts.otc_fund.ledger import run_chronological_simulation
    from scripts.otc_fund.cashflows import build_cashflow_schedule
    
    div_csv = os.path.join(REPO_ROOT, "data", "otc_fund", "dividend_events.csv")
    proxy_csv = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "asset_class_proxy_panel_2015_2026.csv")
    assert os.path.exists(div_csv), "dividend_events.csv must exist"
    assert os.path.exists(proxy_csv), "proxy panel must exist"
    
    df_proxy = pd.read_csv(proxy_csv, index_col=0, parse_dates=True)
    div_df = pd.read_csv(div_csv, parse_dates=["date"])
    
    # Check 100032 dividends exist
    div_100032 = div_df[div_df["target_column"] == "dividend_100032"]
    assert len(div_100032) >= 10, "100032 must have at least 10 dividend events"
    
    # Run a test window around the 2016-02-02 dividend (0.35 RMB per share)
    dates = df_proxy.index[(df_proxy.index >= "2016-01-04") & (df_proxy.index <= "2016-02-15")]
    cfs = {dates[0]: 100000.0}
    weights = {"dividend_100032": 1.0}
    
    ledger_no_div, res_no_div = run_chronological_simulation(dates, df_proxy, cfs, weights, sub_fee=0.0, dividend_events=pd.DataFrame())
    ledger_with_div, res_with_div = run_chronological_simulation(dates, df_proxy, cfs, weights, sub_fee=0.0, dividend_events=div_df)
    
    # After 2016-02-02, shares with dividend reinvestment MUST exceed shares without
    shares_no_div = ledger_no_div.get_shares("dividend_100032")
    shares_with_div = ledger_with_div.get_shares("dividend_100032")
    assert shares_with_div > shares_no_div, f"Shares must increase after reinvestment: with={shares_with_div}, without={shares_no_div}"
    
    # Final asset value with dividend reinvestment MUST be strictly higher than without
    assert res_with_div["total_asset"].iloc[-1] > res_no_div["total_asset"].iloc[-1]

