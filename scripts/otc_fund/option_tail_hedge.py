# -*- coding: utf-8 -*-
"""
Option Tail-Risk Hedging Simulation Module
==========================================
Models protective out-of-the-money (OTM) put option tail-risk hedging:
- Annualized insurance premium budget: 0.5% - 1.5% of equity exposure.
- Payout triggers during severe equity market crashes (e.g. 2015 crash, 2018 drop).
- Evaluates cost-of-carry drag vs drawdown protection.
"""

from typing import Dict, List, Tuple
import numpy as np
import pandas as pd

def simulate_tail_hedge_payout(equity_returns: pd.Series,
                               strike_otm_pct: float = -0.10,
                               annual_budget_pct: float = 0.01) -> pd.Series:
    """
    Simulates monthly rolling protective put overlay on equity holdings.
    - strike_otm_pct: OTM threshold for crash payout (e.g. -10% monthly drop).
    - annual_budget_pct: cost of insurance deducted pro-rata daily (e.g. 1.0% annual).
    """
    daily_premium_drag = (1.0 + annual_budget_pct) ** (1.0 / 252.0) - 1.0
    
    # Monthly returns for payoff calculation
    payout_series = pd.Series(0.0, index=equity_returns.index)
    
    # Deduct daily insurance premium
    payout_series -= daily_premium_drag
    
    # Check for severe drawdown days where put options generate convex payoff
    crash_days = equity_returns[equity_returns < (strike_otm_pct / 5.0)]
    for dt, ret in crash_days.items():
        # Convex payoff when daily return drops below strike threshold
        payout = abs(ret - strike_otm_pct / 5.0) * 0.5
        payout_series.loc[dt] += payout
        
    return payout_series
