# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.instruments import CORE_FUNDS

def test_no_backward_filling():
    """Verify that there is strictly zero backward fill across inception boundaries."""
    csv_path = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "fund_true_nav_panel_2015_2026.csv")
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    
    for code, meta in CORE_FUNDS.items():
        col = f"{meta.category}_{code}"
        incept_dt = pd.Timestamp(meta.first_available_date)
        
        # 10 days before inception must be completely NaN
        pre_window = df.loc[(df.index < incept_dt) & (df.index >= incept_dt - pd.Timedelta(days=30)), col]
        if not pre_window.empty:
            assert pre_window.isna().all(), f"Found backward fill for {code} in the 30 days prior to inception!"
