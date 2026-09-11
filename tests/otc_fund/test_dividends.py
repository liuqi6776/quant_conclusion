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
