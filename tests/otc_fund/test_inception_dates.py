# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.instruments import CORE_FUNDS
from scripts.otc_fund.ledger import ForwardLedger

def test_true_panel_inception_nans():
    """Verify that in the true fund panel, values before first_available_date are strictly NaN."""
    csv_path = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "fund_true_nav_panel_2015_2026.csv")
    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    
    for code, meta in CORE_FUNDS.items():
        col = f"{meta.category}_{code}"
        assert col in df.columns, f"Column {col} missing in true fund panel"
        
        incept_dt = pd.Timestamp(meta.first_available_date)
        pre_incept_series = df.loc[df.index < incept_dt, col]
        
        if not pre_incept_series.empty:
            assert pre_incept_series.isna().all(), (
                f"Fund {code} ({meta.name}) has non-NaN values before first_available_date {meta.first_available_date}! "
                f"First non-NaN at {pre_incept_series.dropna().index[0]}"
            )

def test_trading_pre_inception_rejected():
    """Verify that ForwardLedger rejects purchasing a fund with NaN NAV before inception."""
    ledger = ForwardLedger(cash=10000.0)
    dt_pre = pd.Timestamp("2015-06-01")
    
    # 017730 incepted in 2023-01-30, NAV in 2015 is NaN
    with pytest.raises(ValueError, match="is invalid"):
        ledger.buy("017730", dt_pre, unit_nav=np.nan, amount=1000.0)
