# -*- coding: utf-8 -*-
"""
Target Volatility Risk Budgeting Module
======================================
Strictly enforces:
1. Only T-1 known data used for calculating rolling volatility (no lookahead).
2. Target annualized volatility (e.g. 7.0%).
3. Risk asset scaling with cash / money-market buffer.
4. Redemption fees deducted via FIFO when de-leveraging/reducing exposure.
5. Dual mode support:
   - "open_loop": Standard inverse-volatility multiplier (legacy baseline).
   - "proportional_control": Closed-loop feedback controller (Kp=0.25)
     dampening high-frequency noise, slashing turnover and redemption fee drag.
"""

from typing import Dict, List, Tuple, Optional, Any, Union
import numpy as np
import pandas as pd

from .ledger import ForwardLedger
from .metrics import calc_twr_curve, calc_volatility_and_sharpe

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
                              sub_fee: float = 0.0015,
                              mode: str = "open_loop",
                              kp: float = 0.25,
                              deadband: float = 0.0,
                              return_diagnostics: bool = False) -> Union[Tuple[ForwardLedger, pd.DataFrame], Tuple[ForwardLedger, pd.DataFrame, Dict[str, Any]]]:
    """
    Run volatility targeted strategy where portfolio leverage/exposure
    is scaled by target_vol vs realized rolling vol(T-1), bounded in [min_weight, max_weight].
    Residual capital is held in cash / money market fund.

    Parameters:
    -----------
    trading_dates: pd.DatetimeIndex
        Simulation calendar.
    nav_df: pd.DataFrame
        Asset unit NAVs panel.
    cashflow_schedule: Dict[pd.Timestamp, float]
        External cash deposits (lump sum + monthly DCA).
    base_weights: Dict[str, float]
        Target allocation proportions among risk assets.
    target_vol: float
        Target annualized volatility (default 0.07 = 7.0%).
    vol_window: int
        Rolling window for volatility estimation (default 60 days).
    min_weight: float
        Lower bound on risk asset exposure multiplier (default 0.30).
    max_weight: float
        Upper bound on risk asset exposure multiplier (default 1.00).
    sub_fee: float
        Default front-end subscription fee rate (0.0015 = 0.15%).
    mode: str
        "open_loop" (default legacy) or "proportional_control" / "pc".
    kp: float
        Proportional feedback gain for "proportional_control" (default 0.25).
    deadband: float
        Tolerance threshold below which multiplier adjustments are ignored (default 0.0).
    return_diagnostics: bool
        If True, returns (ledger, df, diagnostics_dict). Default False.
    """
    ledger = ForwardLedger()
    
    # Compute daily asset returns
    returns_df = nav_df.pct_change()
    rolling_vols = calc_rolling_portfolio_vol(returns_df, base_weights, window=vol_window)
    
    multiplier = float(np.clip(1.0, min_weight, max_weight))
    multiplier_history: List[float] = []
    monthly_multipliers: Dict[pd.Timestamp, float] = {}
    
    for dt in trading_dates:
        daily_px = {col: nav_df.loc[dt, col] for col in base_weights.keys() if col in nav_df.columns}
        
        # Step 1: Process scheduled cash deposits
        if dt in cashflow_schedule:
            deposit_amt = cashflow_schedule[dt]
            ledger.deposit(dt, deposit_amt)
            
        # Step 2: Determine target risk multiplier based on T-1 known volatility
        rv = rolling_vols.loc[dt] if dt in rolling_vols.index else np.nan
        if np.isfinite(rv) and rv > 0.01:
            target_multiplier = float(np.clip(target_vol / rv, min_weight, max_weight))
        else:
            target_multiplier = float(np.clip(1.0, min_weight, max_weight))
            
        # Monthly rebalance to target exposure (on first trading day of month)
        is_first_day_of_month = (dt == trading_dates[0]) or (dt.month != trading_dates[trading_dates.get_loc(dt) - 1].month)
        
        if is_first_day_of_month:
            if mode == "open_loop":
                multiplier = target_multiplier
            elif mode in ("proportional_control", "pc"):
                if dt == trading_dates[0]:
                    multiplier = target_multiplier
                else:
                    if abs(target_multiplier - multiplier) >= deadband:
                        multiplier = float(np.clip((1.0 - kp) * multiplier + kp * target_multiplier, min_weight, max_weight))
            else:
                raise ValueError(f"Unknown vol target mode: {mode}")
                
            monthly_multipliers[dt] = multiplier
            cur_mv = sum(ledger.get_shares(c) * daily_px[c] for c in base_weights.keys() if np.isfinite(daily_px.get(c, np.nan)))
            cur_tot = ledger.cash + cur_mv
            
            # Scaled weights
            scaled_weights = {c: w * multiplier for c, w in base_weights.items()}
            # Credit residual unallocated weight to money market cash buffer
            residual_w = max(0.0, 1.0 - sum(scaled_weights.values()))
            if "money_market_000198" in nav_df.columns and residual_w > 0:
                scaled_weights["money_market_000198"] = scaled_weights.get("money_market_000198", 0.0) + residual_w
            
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
                    fee_rate = 0.0 if code == "money_market_000198" else sub_fee
                    ledger.buy(code, dt, px, needed_amt, sub_fee_rate=fee_rate)
                    
        multiplier_history.append(multiplier)
        
        # Step 3: Record daily close
        day_navs = {col: nav_df.loc[dt, col] for col in nav_df.columns}
        ledger.record_day(dt, day_navs)
        
    df = ledger.to_dataframe()
    df["risk_multiplier"] = multiplier_history
    
    # Performance diagnostics
    cf_s = pd.Series(0.0, index=df.index)
    for d, a in cashflow_schedule.items():
        if d in cf_s.index:
            cf_s.loc[d] = a
    twr_curve = calc_twr_curve(df["total_asset"], cf_s)
    ann_vol, sharpe = calc_volatility_and_sharpe(twr_curve)
    
    m_vals = list(monthly_multipliers.values())
    churn = float(np.abs(np.diff(m_vals)).sum()) if len(m_vals) > 1 else 0.0
    
    diagnostics = {
        "mode": mode,
        "kp": kp,
        "deadband": deadband,
        "target_vol": target_vol,
        "realized_vol": ann_vol,
        "vol_tracking_error": abs(ann_vol - target_vol),
        "multiplier_churn": churn,
        "sub_fees_paid": ledger.total_sub_fees_paid,
        "red_fees_paid": ledger.total_red_fees_paid,
        "total_fees_paid": ledger.total_fees_paid,
        "sharpe_ratio": sharpe,
        "monthly_multipliers": monthly_multipliers
    }
    ledger.diagnostics = diagnostics  # type: ignore
    
    if return_diagnostics:
        return ledger, df, diagnostics
    return ledger, df
