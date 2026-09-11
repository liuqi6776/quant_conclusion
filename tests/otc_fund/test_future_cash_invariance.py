# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.ledger import run_chronological_simulation

def test_future_cash_leaves_past_history_invariant():
    """
    Adding a future deposit at date T_future MUST NOT alter historical valuations for t < T_future.
    """
    dates = pd.date_range("2021-01-04", "2021-04-30", freq="B")
    # Random walk asset
    np.random.seed(42)
    px = 1.0 + np.cumsum(np.random.normal(0.0005, 0.01, len(dates)))
    nav_df = pd.DataFrame({"ASSET_A": px}, index=dates)
    
    # Baseline: deposit 100,000 on day 0 and 5,000 on day 20
    cfs_base = {dates[0]: 100000.0, dates[20]: 5000.0}
    weights = {"ASSET_A": 1.0}
    _, df_base = run_chronological_simulation(dates, nav_df, cfs_base, weights)
    
    # Run 2: add extra 50,000 on day 50 (future)
    cfs_ext = dict(cfs_base)
    cfs_ext[dates[50]] = 50000.0
    _, df_ext = run_chronological_simulation(dates, nav_df, cfs_ext, weights)
    
    # For all days t < dates[50], df_ext MUST exactly match df_base!
    past_mask = dates < dates[50]
    np.testing.assert_allclose(
        df_base.loc[past_mask, "total_asset"].values,
        df_ext.loc[past_mask, "total_asset"].values,
        rtol=1e-7,
        err_msg="Future deposit altered historical portfolio valuation!"
    )
