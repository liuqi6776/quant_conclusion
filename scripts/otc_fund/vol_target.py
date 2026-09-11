# -*- coding: utf-8 -*-
"""
Target Volatility Risk Budgeting Module
======================================
Strictly enforces:
1. Only T-1 known data used for calculating rolling volatility (no lookahead).
2. Target annualized volatility (e.g. 7.0%).
3. Risk asset scaling with cash buffer.
4. Redemption fees deducted via FIFO when de-leveraging/reducing exposure.
"""

from typing import Dict, List, Tuple, Optional
import numpy as np
import pandas as pd

from .ledger import ForwardLedger

def calc_rolling_portfolio_vol(returns_df: pd.DataFrame, 
                               weights: Dict[str, float], 
                               window: int = 60) -> pd.Series:
    """
    Calculate rolling portfolio volatility using strictly lagged (T-1) returns.
    """
    cols = [c for c in weights.keys() if c in returns_df.columns]
    w_vec = np.array([weights[c] for c in cols])
    w_vec = w_vec / w_vec.sum()
    
    # Portfolio daily returns
    sub_rets = returns_df[cols]
    port_rets = sub_rets.dot(w_vec)
    
    # Rolling standard deviation annualized by sqrt(252), shifted by 1 day to guarantee T-1 knowledge
    rolling_vol = port_rets.rolling(window=window).std(ddof=1) * np.sqrt(252)
    return rolling_vol.shift(1)

def run_vol_target_simulation(trading_dates: pd.DatetimeIndex,
                              nav_df: pd.DataFrame,
                              cashflow_schedule: Dict[pd.Timestamp, float],
                              base_weights: Dict[str, float],
                              target_vol: float = 0.07,
                              vol_window: int = 60,
                              min_weight: float = 0.30,
                              max_weight: float = 1.00,
                              sub_fee: float = 0.0015) -> Tuple[ForwardLedger, pd.DataFrame]:
    """
    Run volatility targeted strategy where portfolio leverage/exposure
    is scaled by target_vol / rolling_vol(T-1), bounded in [min_weight, max_weight].
    Residual capital is held in cash / money market fund.
    """
    ledger = ForwardLedger()
    
    # Compute daily asset returns
    returns_df = nav_df.pct_change()
    rolling_vols = calc_rolling_portfolio_vol(returns_df, base_weights, window=vol_window)
    
    for dt in trading_dates:
        daily_px = {col: nav_df.loc[dt, col] for col in base_weights.keys() if col in nav_df.columns}
        
        # Step 1: Process scheduled cash deposits
        if dt in cashflow_schedule:
            deposit_amt = cashflow_schedule[dt]
            ledger.deposit(dt, deposit_amt)
            
        # Step 2: Determine target risk multiplier based on T-1 known volatility
        rv = rolling_vols.loc[dt] if dt in rolling_vols.index else np.nan
        if np.isfinite(rv) and rv > 0.01:
            multiplier = float(np.clip(target_vol / rv, min_weight, max_weight))
        else:
            multiplier = 1.0
            
        # Monthly rebalance to target exposure (on first trading day of month)
        is_first_day_of_month = (dt == trading_dates[0]) or (dt.month != trading_dates[trading_dates.get_loc(dt) - 1].month)
        
        if is_first_day_of_month:
            cur_mv = sum(ledger.get_shares(c) * daily_px[c] for c in base_weights.keys() if np.isfinite(daily_px.get(c, np.nan)))
            cur_tot = ledger.cash + cur_mv
            
            # Scaled weights
            scaled_weights = {c: w * multiplier for c, w in base_weights.items()}
            
            # Rebalance: sell overweighted
            for code, target_w in scaled_weights.items():
                px = daily_px.get(code, np.nan)
                if not np.isfinite(px) or px <= 0:
                    continue
                target_val = cur_tot * target_w
                cur_val = ledger.get_shares(code) * px
                if cur_val > target_val + 1.0:
                    excess_sh = (cur_val - target_val) / px
                    ledger.sell(code, dt, px, excess_sh)
                    
            # Buy underweighted
            for code, target_w in scaled_weights.items():
                px = daily_px.get(code, np.nan)
                if not np.isfinite(px) or px <= 0:
                    continue
                target_val = cur_tot * target_w
                cur_val = ledger.get_shares(code) * px
                if cur_val < target_val - 1.0 and ledger.cash > 1.0:
                    needed_amt = min(target_val - cur_val, ledger.cash)
                    ledger.buy(code, dt, px, needed_amt, sub_fee_rate=sub_fee)
                    
        # Step 3: Record daily close
        day_navs = {col: nav_df.loc[dt, col] for col in nav_df.columns}
        ledger.record_day(dt, day_navs)
        
    return ledger, ledger.to_dataframe()
