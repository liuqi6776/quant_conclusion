# -*- coding: utf-8 -*-
"""
Strict Chronological Forward Event-Driven Ledger
================================================
Guarantees:
1. Strictly forward, single-pass simulation over trading days.
2. Future deposits are unknown and NEVER affect past portfolio states.
3. Execution strictly uses unit_nav (never acc_nav).
4. Explicit handling of cash dividends and dividend reinvestment with verified continuity.
5. FIFO redemption fee lot tracking.
"""
import os
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np

from .instruments import get_instrument, InstrumentMeta
from .fees import calc_sub_fee, calc_fifo_redemption

class Lot:
    __slots__ = ("shares", "purchase_date", "purchase_nav")
    def __init__(self, shares: float, purchase_date: pd.Timestamp, purchase_nav: float):
        self.shares = float(shares)
        self.purchase_date = pd.Timestamp(purchase_date)
        self.purchase_nav = float(purchase_nav)

class ForwardLedger:
    """
    Event-driven multi-asset portfolio accounting ledger.
    """
    def __init__(self, cash: float = 0.0):
        self.cash = float(cash)
        self.cumulative_invested = float(cash)
        self.lots: Dict[str, List[Lot]] = {}
        
        # Daily history records
        self.history_dates: List[pd.Timestamp] = []
        self.history_cash: List[float] = []
        self.history_invested: List[float] = []
        self.history_market_val: List[float] = []
        self.history_total_asset: List[float] = []
        self.history_shares: Dict[str, List[float]] = {}
        
    def get_shares(self, code: str) -> float:
        return sum(lot.shares for lot in self.lots.get(code, []))
        
    def deposit(self, date: pd.Timestamp, amount: float):
        """Add external cash capital to ledger on date."""
        if amount <= 0:
            return
        self.cash += amount
        self.cumulative_invested += amount
        
    def buy(self, code: str, date: pd.Timestamp, unit_nav: float, amount: float, sub_fee_rate: float = 0.0015):
        """
        Execute purchase of a fund at unit_nav.
        Enforces inception date constraint: raises ValueError if unit_nav is NaN or non-positive.
        """
        if amount <= 0:
            return 0.0
            
        if self.cash < amount - 1e-6:
            raise ValueError(f"Insufficient cash on {date}: requested {amount:.2f}, available {self.cash:.2f}")
            
        if not np.isfinite(unit_nav) or unit_nav <= 0:
            raise ValueError(f"Cannot buy {code} on {date}: unit_nav {unit_nav} is invalid (fund not incepted or unpriced).")
            
        net_inv, fee = calc_sub_fee(amount, sub_fee_rate)
        new_shares = net_inv / unit_nav
        
        self.cash -= amount
        self.lots.setdefault(code, []).append(Lot(new_shares, date, unit_nav))
        return new_shares
        
    def sell(self, code: str, date: pd.Timestamp, unit_nav: float, shares_to_sell: float) -> Tuple[float, float]:
        """
        Sell shares using FIFO lot deduction and statutory redemption fee tiers.
        Returns: (gross_proceeds, net_proceeds)
        """
        cur_shares = self.get_shares(code)
        sell_qty = min(shares_to_sell, cur_shares)
        if sell_qty <= 0:
            return 0.0, 0.0
            
        lot_tuples = [(lot.shares, lot.purchase_date, lot.purchase_nav) for lot in self.lots.get(code, [])]
        gross, net, remaining_tuples = calc_fifo_redemption(lot_tuples, sell_qty, date, unit_nav)
        
        self.lots[code] = [Lot(sh, d, p) for sh, d, p in remaining_tuples]
        self.cash += net
        return gross, net
        
    def process_dividend(self, code: str, date: pd.Timestamp, unit_nav: float, dividend_per_share: float, mode: str = "reinvest"):
        """
        Process dividend event.
        - reinvest: converts total payout into new shares at unit_nav with zero subscription fee.
        - cash: deposits total payout into account cash balance.
        In both modes, total portfolio asset value is strictly continuous across the dividend.
        """
        cur_shares = self.get_shares(code)
        if cur_shares <= 0 or dividend_per_share <= 0:
            return
            
        total_payout = cur_shares * dividend_per_share
        
        if mode == "reinvest":
            if not np.isfinite(unit_nav) or unit_nav <= 0:
                raise ValueError(f"Invalid unit_nav {unit_nav} for dividend reinvestment on {date}")
            new_shares = total_payout / unit_nav
            # Added as dividend reinvestment lot (inherits dividend date, 0 subscription fee)
            self.lots.setdefault(code, []).append(Lot(new_shares, date, unit_nav))
        elif mode == "cash":
            self.cash += total_payout
        else:
            raise ValueError(f"Unknown dividend mode: {mode}")
            
    def record_day(self, date: pd.Timestamp, daily_unit_navs: Dict[str, float]):
        """
        Calculate closing market value and record state for date.
        """
        mv = 0.0
        for code, lots in self.lots.items():
            sh = sum(lot.shares for lot in lots)
            self.history_shares.setdefault(code, []).append(sh)
            if sh > 0:
                nv = daily_unit_navs.get(code, np.nan)
                if np.isfinite(nv) and nv > 0:
                    mv += sh * nv
                else:
                    # If position exists but nav is missing, throw error
                    raise ValueError(f"Missing unit_nav for held asset {code} on {date}")
                    
        tot_asset = self.cash + mv
        self.history_dates.append(date)
        self.history_cash.append(self.cash)
        self.history_invested.append(self.cumulative_invested)
        self.history_market_val.append(mv)
        self.history_total_asset.append(tot_asset)
        
    def to_dataframe(self) -> pd.DataFrame:
        """Export daily history as a structured pandas DataFrame."""
        df = pd.DataFrame({
            "cash": self.history_cash,
            "cumulative_invested": self.history_invested,
            "market_value": self.history_market_val,
            "total_asset": self.history_total_asset
        }, index=pd.DatetimeIndex(self.history_dates))
        for code, sh_list in self.history_shares.items():
            df[f"shares_{code}"] = sh_list
        return df

def run_chronological_simulation(trading_dates: pd.DatetimeIndex,
                                 nav_df: pd.DataFrame,
                                 cashflow_schedule: Dict[pd.Timestamp, float],
                                 target_weights: Dict[str, float],
                                 sub_fee: float = 0.0015,
                                 rebalance_freq: Optional[str] = None,
                                 dividend_events: Optional[pd.DataFrame] = None) -> Tuple[ForwardLedger, pd.DataFrame]:
    """
    Strict single-pass chronological simulation.
    Iterates day by day:
    1. Process dividends for existing held lots (reinvested at ex-nav with 0 fee).
    2. Cash deposit on dt if scheduled.
    3. Buy / allocate on dt using known unit_nav.
    4. Rebalance if scheduled.
    5. Record closing valuation.
    """
    ledger = ForwardLedger()
    
    # Auto-load dividend events if not explicitly passed
    if dividend_events is None:
        div_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "otc_fund", "dividend_events.csv")
        if os.path.exists(div_csv):
            dividend_events = pd.read_csv(div_csv, parse_dates=["date"])
            
    div_map = {}
    if dividend_events is not None and not dividend_events.empty:
        for dt_val, grp in dividend_events.groupby(pd.to_datetime(dividend_events["date"])):
            div_map[pd.Timestamp(dt_val)] = grp
            
    # Pre-identify rebalancing dates if periodic rebalance enabled
    rebal_dates = set()
    if rebalance_freq == "quarterly":
        for (y, q), grp in pd.DataFrame(index=trading_dates).groupby([trading_dates.year, trading_dates.quarter]):
            rebal_dates.add(grp.index[0])
            
    for dt in trading_dates:
        # Step 0: Process dividend events for existing holdings as of day start
        if dt in div_map:
            grp = div_map[dt]
            for _, row in grp.iterrows():
                tgt_col = str(row.get("target_column") or row.get("code"))
                div_amt = float(row["dividend_per_share"])
                if ledger.get_shares(tgt_col) > 0:
                    px = nav_df.loc[dt, tgt_col] if tgt_col in nav_df.columns else np.nan
                    if np.isfinite(px) and px > 0:
                        ledger.process_dividend(tgt_col, dt, px, div_amt, mode="reinvest")
                        
        # Step 1: Check and deposit external cash
        if dt in cashflow_schedule:
            deposit_amt = cashflow_schedule[dt]
            ledger.deposit(dt, deposit_amt)
            
            # Allocate newly deposited cash according to target weights
            daily_px = {col: nav_df.loc[dt, col] for col in target_weights.keys() if col in nav_df.columns}
            for code, weight in target_weights.items():
                alloc = deposit_amt * weight
                px = daily_px.get(code, np.nan)
                if np.isfinite(px) and px > 0:
                    ledger.buy(code, dt, px, alloc, sub_fee_rate=sub_fee)

                    
        # Step 2: Periodic Rebalance (if scheduled and after initial day)
        if rebalance_freq and dt in rebal_dates and dt != trading_dates[0]:
            daily_px = {col: nav_df.loc[dt, col] for col in target_weights.keys() if col in nav_df.columns}
            # Current total valuation
            cur_mv = sum(ledger.get_shares(c) * daily_px[c] for c in target_weights.keys() if np.isfinite(daily_px.get(c, np.nan)))
            cur_tot = ledger.cash + cur_mv
            
            # Sell overweighted positions first
            for code, target_w in target_weights.items():
                px = daily_px.get(code, np.nan)
                if not np.isfinite(px) or px <= 0:
                    continue
                target_val = cur_tot * target_w
                cur_val = ledger.get_shares(code) * px
                if cur_val > target_val + 1.0: # sell excess
                    excess_sh = (cur_val - target_val) / px
                    ledger.sell(code, dt, px, excess_sh)
                    
            # Buy underweighted positions with available cash
            for code, target_w in target_weights.items():
                px = daily_px.get(code, np.nan)
                if not np.isfinite(px) or px <= 0:
                    continue
                target_val = cur_tot * target_w
                cur_val = ledger.get_shares(code) * px
                if cur_val < target_val - 1.0 and ledger.cash > 1.0:
                    needed_amt = min(target_val - cur_val, ledger.cash)
                    ledger.buy(code, dt, px, needed_amt, sub_fee_rate=sub_fee)
                    
        # Step 3: Record end of day valuation
        day_navs = {col: nav_df.loc[dt, col] for col in nav_df.columns}
        ledger.record_day(dt, day_navs)
        
    return ledger, ledger.to_dataframe()
