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


def test_twr_gross_vs_net_fee_convention():
    """Verify that net-of-fees TWR includes front-end fee discount, while gross-of-fees nets it out."""
    dates = pd.date_range("2021-01-01", "2021-01-10", freq="D")
    # Asset has 0 price return, but 1.5 fee paid on 1000 deposit on day 2
    # On day 1: deposit 1000, value 998.5 (after 1.5 fee)
    # On day 2: flat
    val_s = pd.Series(998.5, index=dates)
    cf_s = pd.Series(0.0, index=dates)
    cf_s.loc[dates[0]] = 1000.0
    sub_fee_s = pd.Series(0.0, index=dates)
    sub_fee_s.loc[dates[0]] = 1.5
    
    # Net of fees (default)
    twr_net = calc_twr_curve(val_s, cf_s, net_sub_fee=True)
    assert pytest.approx(twr_net.iloc[0], rel=1e-4) == 1.0
    
    # Gross of fees: eff_cf = cf - fee = 1000 - 1.5 = 998.5
    # When val is 998.5, gross return is exactly 0.0
    val_s_day2 = val_s.copy()
    val_s_day2.iloc[1:] = 1000.0
    cf_s.loc[dates[1]] = 1000.0
    val_s_day2.iloc[1:] = 998.5 + 998.5 # 1997.0
    sub_fee_s.loc[dates[1]] = 1.5
    
    twr_gross = calc_twr_curve(val_s_day2, cf_s, net_sub_fee=False, sub_fee_series=sub_fee_s)
    # Gross TWR should remain exactly 1.0 because underlying asset had 0 return
    np.testing.assert_allclose(twr_gross.values, 1.0, rtol=1e-4)

