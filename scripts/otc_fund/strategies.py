# -*- coding: utf-8 -*-
"""
Portfolio Allocation Strategies
==============================
Implements systematic allocation rules:
1. Static Allocation (buy-and-hold + target-weighted recurring DCA).
2. New-Cash-Only Drift Rebalancing ("新钱平衡旧钱" - zero redemption cost).
3. Periodic Full Rebalancing (quarterly/semi-annually with FIFO fee deductions).
4. VolTarget Risk Budgeting (uses strictly T-1 historical volatility).
"""

from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

from .instruments import CORE_FUNDS, RESEARCH_PROXIES
from .ledger import ForwardLedger
from .fees import calc_sub_fee

def get_static_9_asset_weights() -> Dict[str, float]:
    """Canonical 9-Asset Target Weights."""
    return {
        "bond_pure_000015": 0.15,
        "bond_qdii_004998": 0.10,
        "dividend_100032": 0.10,
        "money_market_000198": 0.10,
        "quant_a_001917": 0.10,
        "gold_000216": 0.15,
        "nasdaq_000834": 0.15,
        "global_tech_017730": 0.10,
        "oil_501018": 0.05
    }

def get_modified_7_asset_weights() -> Dict[str, float]:
    """Modified 7-Asset Target Weights (Domestic Bond replaces QDII Bond, Gold replaces Oil)."""
    return {
        "bond_pure_000015": 0.25,
        "dividend_100032": 0.10,
        "money_market_000198": 0.10,
        "quant_a_001917": 0.10,
        "gold_000216": 0.20,
        "nasdaq_000834": 0.15,
        "global_tech_017730": 0.10
    }

def run_new_cash_rebalancing(trading_dates: pd.DatetimeIndex,
                             nav_df: pd.DataFrame,
                             cashflow_schedule: Dict[pd.Timestamp, float],
                             target_weights: Dict[str, float],
                             sub_fee: float = 0.0015) -> Tuple[ForwardLedger, pd.DataFrame]:
    """
    New-Cash-Only Rebalancing Strategy:
    When new external DCA cash arrives, instead of buying all assets pro-rata,
    it calculates the current portfolio weights and directs new cash preferentially
    to the most underweighted assets. Never sells existing holdings (zero redemption fee).
    """
    ledger = ForwardLedger()
    
    for dt in trading_dates:
        daily_px = {col: nav_df.loc[dt, col] for col in target_weights.keys() if col in nav_df.columns}
        
        if dt in cashflow_schedule:
            deposit_amt = cashflow_schedule[dt]
            ledger.deposit(dt, deposit_amt)
            
            # Initial day: allocate strictly according to target weights
            if dt == trading_dates[0]:
                for code, w in target_weights.items():
                    px = daily_px.get(code, np.nan)
                    if np.isfinite(px) and px > 0:
                        ledger.buy(code, dt, px, deposit_amt * w, sub_fee_rate=sub_fee)
            else:
                # Calculate current market value of each holding
                cur_values = {}
                tot_val = ledger.cash
                for code in target_weights.keys():
                    px = daily_px.get(code, np.nan)
                    val = ledger.get_shares(code) * px if np.isfinite(px) and px > 0 else 0.0
                    cur_values[code] = val
                    tot_val += val
                    
                # Target value after deposit
                target_vals = {c: tot_val * w for c, w in target_weights.items()}
                # Shortfalls (underweighted amounts)
                shortfalls = {c: max(0.0, target_vals[c] - cur_values[c]) for c in target_weights.keys()}
                tot_shortfall = sum(shortfalls.values())
                
                if tot_shortfall > 1.0:
                    for code in target_weights.keys():
                        alloc = deposit_amt * (shortfalls[code] / tot_shortfall)
                        px = daily_px.get(code, np.nan)
                        if alloc > 1.0 and np.isfinite(px) and px > 0 and ledger.cash >= alloc:
                            ledger.buy(code, dt, px, alloc, sub_fee_rate=sub_fee)
                else:
                    # If all on target, allocate pro-rata
                    for code, w in target_weights.items():
                        alloc = deposit_amt * w
                        px = daily_px.get(code, np.nan)
                        if alloc > 1.0 and np.isfinite(px) and px > 0 and ledger.cash >= alloc:
                            ledger.buy(code, dt, px, alloc, sub_fee_rate=sub_fee)
                            
        # Close day
        day_navs = {col: nav_df.loc[dt, col] for col in nav_df.columns}
        ledger.record_day(dt, day_navs)
        
    return ledger, ledger.to_dataframe()
