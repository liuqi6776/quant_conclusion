# -*- coding: utf-8 -*-
# WARNING: DEPRECATED PROTOTYPE / 模型有误，严禁实盘使用
"""
Option Tail-Risk Hedging Simulation Module (DEPRECATED)
======================================================
WARNING: DEPRECATED PROTOTYPE / 模型有误，严禁实盘使用
This module is a legacy conceptual prototype that lacks rigorous implied
volatility skew, Greeks dynamics, and calendar theta decay modeling.
Runtime execution is disabled.
"""

from typing import Dict, List, Tuple
import warnings
import numpy as np
import pandas as pd

def simulate_tail_hedge_payout(equity_returns: pd.Series,
                               strike_otm_pct: float = -0.10,
                               annual_budget_pct: float = 0.01) -> pd.Series:
    """
    Simulates monthly rolling protective put overlay on equity holdings.
    Deprecated: Raises NotImplementedError upon invocation.
    """
    warnings.warn(
        "option_tail_hedge is a deprecated heuristic prototype and strictly disabled.",
        DeprecationWarning,
        stacklevel=2,
    )
    raise NotImplementedError(
        "option_tail_hedge is a deprecated heuristic prototype and disabled for live trading. "
        "Real implied volatility surface and theta decay modeling required."
    )
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
