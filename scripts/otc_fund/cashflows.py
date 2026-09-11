# -*- coding: utf-8 -*-
"""
DCA and Portfolio External Cash Flow Schedule Generator
=======================================================
Generates exact trade execution dates and external cash flows.
Ensures zero lookahead bias and rigorous distinction between monthly and weekly plans.
"""

from typing import List, Dict, Union
import pandas as pd
import numpy as np

def generate_monthly_dca_dates(trading_index: pd.DatetimeIndex) -> List[pd.Timestamp]:
    """
    Generate monthly DCA dates: exactly the first available trading day of each calendar month.
    """
    dca_dates = []
    df_temp = pd.DataFrame(index=trading_index)
    for (year, month), grp in df_temp.groupby([trading_index.year, trading_index.month]):
        dca_dates.append(grp.index[0])
    return sorted(dca_dates)

def generate_weekly_dca_dates(trading_index: pd.DatetimeIndex) -> List[pd.Timestamp]:
    """
    Generate weekly DCA dates: first available trading day of each calendar week (typically Monday).
    """
    dca_dates = []
    df_temp = pd.DataFrame(index=trading_index)
    # Group by ISO calendar (year, week)
    for (year, week), grp in df_temp.groupby([trading_index.isocalendar().year, trading_index.isocalendar().week]):
        dca_dates.append(grp.index[0])
    return sorted(dca_dates)

def build_cashflow_schedule(trading_index: pd.DatetimeIndex,
                            initial_lump: float = 1000000.0,
                            dca_amount: float = 10000.0,
                            dca_freq: str = "monthly",
                            dca_start_delay_months: int = 0) -> Dict[pd.Timestamp, float]:
    """
    Build a complete dictionary of {date: deposit_amount} for external cash additions.
    dca_freq: 'monthly' (10,000 RMB standard) or 'weekly' (3,150 RMB standard).
    """
    schedule: Dict[pd.Timestamp, float] = {}
    d0 = trading_index[0]
    
    if initial_lump > 0:
        schedule[d0] = initial_lump
        
    if dca_freq == "monthly":
        dca_dates = generate_monthly_dca_dates(trading_index)
    elif dca_freq == "weekly":
        dca_dates = generate_weekly_dca_dates(trading_index)
    else:
        raise ValueError(f"Unsupported dca_freq: {dca_freq}")
        
    for dt in dca_dates:
        # If lump sum on d0 and dca_start_delay_months > 0, skip initial overlapping month
        if dt == d0 and initial_lump > 0 and dca_start_delay_months > 0:
            continue
        schedule[dt] = schedule.get(dt, 0.0) + dca_amount
        
    return schedule
