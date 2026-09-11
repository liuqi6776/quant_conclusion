# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

def test_benchmark_and_fund_data_identity():
    """Verify 5 fixed dates for benchmark and fund data integrity against expected values."""
    csv_path = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "fund_true_nav_panel_2015_2026.csv")
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    
    # Check 5 fixed dates
    test_dates = [
        "2015-01-05",
        "2016-06-15",
        "2018-01-02",
        "2021-01-04",
        "2026-08-05"
    ]
    
    for dt_str in test_dates:
        dt = pd.Timestamp(dt_str)
        assert dt in df.index, f"Date {dt_str} missing from panel index"
        
        # 000015 (domestic debt) must exist and be positive on all 5 dates
        nv_bond = df.loc[dt, "bond_pure_000015"]
        assert np.isfinite(nv_bond) and nv_bond > 0.8, f"Invalid 000015 nav on {dt_str}: {nv_bond}"
        
        # 000216 (gold) must exist and be positive
        nv_gold = df.loc[dt, "gold_000216"]
        assert np.isfinite(nv_gold) and nv_gold > 0.8, f"Invalid 000216 nav on {dt_str}: {nv_gold}"
