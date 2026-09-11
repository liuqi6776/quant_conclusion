# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.fees import get_redemption_fee_rate, calc_fifo_redemption

def test_statutory_redemption_fee_tiers():
    assert get_redemption_fee_rate(0) == 0.015
    assert get_redemption_fee_rate(6) == 0.015
    assert get_redemption_fee_rate(7) == 0.005
    assert get_redemption_fee_rate(364) == 0.005
    assert get_redemption_fee_rate(365) == 0.0025
    assert get_redemption_fee_rate(729) == 0.0025
    assert get_redemption_fee_rate(730) == 0.0
    assert get_redemption_fee_rate(1000) == 0.0

def test_fifo_lot_deduction_order():
    # Lot 1: bought 100 days ago (fee 0.5%)
    # Lot 2: bought 5 days ago (fee 1.5%)
    now = pd.Timestamp("2021-06-01")
    lots = [
        (1000.0, now - pd.Timedelta(days=100), 1.0),
        (500.0, now - pd.Timedelta(days=5), 1.0)
    ]
    
    # Sell 800 shares: completely from Lot 1 (fee 0.5%)
    gross, net, remaining = calc_fifo_redemption(lots, 800.0, now, current_nav=2.0)
    assert gross == 1600.0
    assert net == 1600.0 * (1.0 - 0.005)
    assert remaining[0][0] == 200.0 # Lot 1 has 200 shares remaining
    assert remaining[1][0] == 500.0 # Lot 2 untouched
