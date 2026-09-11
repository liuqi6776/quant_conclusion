# -*- coding: utf-8 -*-
"""
OTC Mutual Fund Fee Model
=========================
Implements front-end subscription fee and statutory FIFO holding-period redemption fee tiers:
- Holding < 7 days: 1.50% (punitive fee under CSRC regulations)
- Holding 7 - 365 days: 0.50%
- Holding 365 - 730 days: 0.25%
- Holding >= 730 days: 0.00%
"""

from typing import List, Tuple
import pandas as pd

DEFAULT_SUB_FEE = 0.0015  # 0.15% subscription fee on 3rd-party platforms

def calc_sub_fee(amount: float, sub_fee_rate: float = DEFAULT_SUB_FEE) -> Tuple[float, float]:
    """
    Given total subscription cash amount, return (net_investment, fee).
    net_investment = amount / (1 + sub_fee_rate) or amount * (1 - sub_fee_rate) standard approximation.
    In OTC platform convention: net_investment = amount * (1 - sub_fee_rate).
    """
    fee = amount * sub_fee_rate
    net_inv = amount - fee
    return net_inv, fee

def get_redemption_fee_rate(holding_days: int) -> float:
    """Standard tiered redemption fee based on holding days."""
    if holding_days < 7:
        return 0.015
    elif holding_days < 365:
        return 0.005
    elif holding_days < 730:
        return 0.0025
    else:
        return 0.0

def calc_fifo_redemption(lots: List[Tuple[float, pd.Timestamp, float]], 
                         sell_shares: float, 
                         current_date: pd.Timestamp, 
                         current_nav: float) -> Tuple[float, float, List[Tuple[float, pd.Timestamp, float]]]:
    """
    Execute FIFO redemption across historical purchase lots.
    Each lot: (shares, purchase_date, purchase_nav)
    Returns: (gross_proceeds, net_proceeds, remaining_lots)
    """
    if sell_shares <= 0:
        return 0.0, 0.0, list(lots)
    
    remaining_sell = sell_shares
    gross_proceeds = 0.0
    net_proceeds = 0.0
    new_lots = []
    
    for sh, p_date, p_nav in lots:
        if remaining_sell <= 0:
            new_lots.append((sh, p_date, p_nav))
            continue
        
        holding_days = (current_date - p_date).days
        fee_rate = get_redemption_fee_rate(holding_days)
        
        if sh <= remaining_sell:
            lot_gross = sh * current_nav
            lot_net = lot_gross * (1.0 - fee_rate)
            gross_proceeds += lot_gross
            net_proceeds += lot_net
            remaining_sell -= sh
        else:
            lot_gross = remaining_sell * current_nav
            lot_net = lot_gross * (1.0 - fee_rate)
            gross_proceeds += lot_gross
            net_proceeds += lot_net
            new_lots.append((sh - remaining_sell, p_date, p_nav))
            remaining_sell = 0.0
            
    return gross_proceeds, net_proceeds, new_lots
