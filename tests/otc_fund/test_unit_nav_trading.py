# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.ledger import ForwardLedger

def test_unit_nav_execution_and_shares():
    """Verify that ledger strictly uses unit_nav to compute executed shares."""
    ledger = ForwardLedger(cash=10000.0)
    dt = pd.Timestamp("2021-01-05")
    
    # Buy 10,000 RMB with 0.15% subscription fee: net investment = 9985.0 RMB
    # Unit NAV = 1.2500 -> Shares = 9985.0 / 1.2500 = 7988.0 shares
    sh = ledger.buy("000015", dt, unit_nav=1.2500, amount=10000.0, sub_fee_rate=0.0015)
    
    assert pytest.approx(sh, rel=1e-5) == 7988.0
    assert pytest.approx(ledger.get_shares("000015"), rel=1e-5) == 7988.0
    assert ledger.cash == 0.0

def test_zero_or_negative_unit_nav_rejected():
    """Verify that non-positive unit_nav raises ValueError."""
    ledger = ForwardLedger(cash=5000.0)
    dt = pd.Timestamp("2021-01-05")
    with pytest.raises(ValueError):
        ledger.buy("000015", dt, unit_nav=0.0, amount=1000.0)
    with pytest.raises(ValueError):
        ledger.buy("000015", dt, unit_nav=-1.2, amount=1000.0)

def test_late_incepted_asset_ledger_alignment():
    """Verify that buying an asset for the first time at day N keeps all history_shares arrays aligned without crashing to_dataframe()."""
    ledger = ForwardLedger(cash=100000.0)
    dates = pd.date_range("2021-01-01", periods=10, freq="B")
    
    # Day 0: Buy asset A
    ledger.buy("asset_A", dates[0], unit_nav=1.0, amount=1000.0)
    for i in range(5):
        ledger.record_day(dates[i], {"asset_A": 1.0})
        
    # Day 5: Buy asset B for the first time
    ledger.buy("asset_B", dates[5], unit_nav=2.0, amount=2000.0)
    for i in range(5, 10):
        ledger.record_day(dates[i], {"asset_A": 1.0, "asset_B": 2.0})
        
    # to_dataframe() should construct without ValueError and asset_B should have 0.0 for first 5 days
    df = ledger.to_dataframe()
    assert len(df) == 10
    assert "asset_B" in ledger.history_shares
    assert len(ledger.history_shares["asset_B"]) == 10
    assert all(ledger.history_shares["asset_B"][i] == 0.0 for i in range(5))
    assert all(ledger.history_shares["asset_B"][i] > 0.0 for i in range(5, 10))

