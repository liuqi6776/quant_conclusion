# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.ledger import run_chronological_simulation

def test_chronological_order_zero_lookahead():
    """
    Zero-return synthetic test specified in audit requirement:
    4 dates, initial 1,000,000, monthly 10,000, fee 0.15%, unit_nav constant 1.0.
    Account path MUST be:
      Day 1: 998,500.00
      Day 2: 1,008,485.00
      Day 3: 1,018,470.00
      Day 4: 1,028,455.00
    First day MUST NEVER show 1,028,455.00!
    """
    dates = pd.to_datetime(["2021-01-04", "2021-02-01", "2021-03-01", "2021-04-01"])
    nav_df = pd.DataFrame({"F1": [1.0, 1.0, 1.0, 1.0]}, index=dates)
    
    cfs = {
        dates[0]: 1000000.0,
        dates[1]: 10000.0,
        dates[2]: 10000.0,
        dates[3]: 10000.0
    }
    
    weights = {"F1": 1.0}
    ledger, res_df = run_chronological_simulation(dates, nav_df, cfs, weights, sub_fee=0.0015)
    
    # Statutory formula net_inv = amount / (1.0 + sub_fee)
    expected = [
        round(1000000.0 / 1.0015, 2),
        round(1000000.0 / 1.0015 + 10000.0 / 1.0015, 2),
        round(1000000.0 / 1.0015 + 20000.0 / 1.0015, 2),
        round(1000000.0 / 1.0015 + 30000.0 / 1.0015, 2)
    ]
    for i, exp in enumerate(expected):
        act = res_df["total_asset"].iloc[i]
        assert pytest.approx(act, abs=0.02) == exp, f"Day {i+1} valuation mismatch: actual {act}, expected {exp}"

