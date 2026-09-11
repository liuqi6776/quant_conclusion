# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.metrics import calc_twr_curve, calc_xirr, calc_max_drawdown

def test_zero_return_asset_twr_is_zero():
    """Zero return asset with arbitrary deposits MUST have TWR strictly equal to 0.0."""
    dates = pd.date_range("2021-01-01", "2021-05-01", freq="D")
    val_s = pd.Series(1000.0, index=dates)
    cf_s = pd.Series(0.0, index=dates)
    cf_s.loc[dates[0]] = 1000.0
    
    # Add large deposit at day 30: valuation jumps from 1000 to 11000
    val_s.iloc[30:] += 10000.0
    cf_s.iloc[30] = 10000.0
    
    twr = calc_twr_curve(val_s, cf_s)
    # Unit curve must remain 1.0 throughout!
    np.testing.assert_allclose(twr.values, 1.0, rtol=1e-6)

def test_xirr_analytical_match():
    """Verify XIRR on known 10% annual return cash flow."""
    d0 = pd.Timestamp("2020-01-01")
    d1 = pd.Timestamp("2021-01-01")
    cfs = [-100.0, 110.0]
    dts = [d0, d1]
    irr = calc_xirr(cfs, dts)
    # 366 days in 2020 leap year -> slightly close to 10%
    assert pytest.approx(irr, rel=0.01) == 0.0997
