# -*- coding: utf-8 -*-
"""
Financial Performance and Risk Metrics Engine
=============================================
Calculates institutional-grade metrics:
1. Money-Weighted Return (MWR): Exact XIRR via Brent's root-finding method.
2. Time-Weighted Return (TWR): Unit value series netting out external cash flows.
3. Standard Maximum Drawdown: Computed strictly on the TWR unit net asset value curve.
4. Custom Capital-Ratio Drawdown: Peak-to-trough decline of (Portfolio Market Value / Invested Capital).
5. Cash-Flow-Adjusted Sharpe Ratio: Derived from daily returns of the TWR unit curve.
6. Annualized Volatility: Standard deviation of TWR daily returns scaled by sqrt(252).
"""

from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import pandas as pd
from scipy.optimize import brentq

def calc_xirr(cash_flows: List[float], dates: List[pd.Timestamp]) -> float:
    """
    Calculate annualized internal rate of return (XIRR).
    cash_flows: negative for deposits, positive for final valuation / withdrawals.
    """
    if len(cash_flows) < 2 or len(dates) < 2:
        return np.nan
    
    d0 = dates[0]
    days = np.array([(d - d0).days for d in dates], dtype=float)
    cfs = np.array(cash_flows, dtype=float)
    
    # Check if there is at least one positive and one negative cash flow
    if (cfs > 0).sum() == 0 or (cfs < 0).sum() == 0:
        return np.nan
        
    def xnpv(r: float) -> float:
        return float(np.sum(cfs / ((1.0 + r) ** (days / 365.0))))
        
    try:
        # Search in [-0.99, 10.0]
        return float(brentq(xnpv, -0.99, 10.0))
    except Exception:
        # Fallback grid search
        rates = np.linspace(-0.5, 2.0, 500)
        vals = [xnpv(r) for r in rates]
        sign_changes = np.where(np.diff(np.sign(vals)))[0]
        if len(sign_changes) > 0:
            idx = sign_changes[0]
            try:
                return float(brentq(xnpv, rates[idx], rates[idx + 1]))
            except Exception:
                pass
        return np.nan

def calc_twr_curve(portfolio_values: pd.Series, 
                   cash_flow_series: pd.Series, 
                   net_sub_fee: bool = True,
                   sub_fee_series: Optional[pd.Series] = None) -> pd.Series:
    """
    Calculate standard Time-Weighted Return (TWR) unit asset value curve (starting at 1.0).
    R_t = (V_t - C_t) / V_{t-1}, where C_t is external net inflow on day t.
    TWR_t = prod(1 + R_tau).

    Fee Convention (M7 / GIPS Presentation):
    - By default (net_sub_fee=True), external cash flow C_t represents gross cash deposit.
      Because OTC mutual fund front-end subscription fees (e.g. 0.15%) are deducted immediately from cash upon deposit,
      the actual portfolio starting value on deposit day is V_t = V_{t-1} + C_t - Fee.
      Consequently, on deposit days: (V_t - C_t) / V_{t-1} reflects a slight initial negative return (-Fee / V_{t-1}).
      This adheres to the Global Investment Performance Standards (GIPS) net-of-fees presentation standard,
      faithfully capturing transaction frictions borne by real investors.
    - If net_sub_fee=False (Gross-of-fees presentation), the subscription fee is added back to
      external cash flow (via sub_fee_series) to evaluate pure underlying asset market returns
      without front-end subscription friction.
    """
    twr_units = pd.Series(1.0, index=portfolio_values.index, dtype=float)
    
    prev_val = 0.0
    cum_unit = 1.0
    
    for i, dt in enumerate(portfolio_values.index):
        val = float(portfolio_values.loc[dt])
        cf = float(cash_flow_series.loc[dt]) if dt in cash_flow_series.index else 0.0
        
        # Adjust external cashflow if gross-of-fees requested
        if not net_sub_fee and sub_fee_series is not None and dt in sub_fee_series.index:
            fee_paid = float(sub_fee_series.loc[dt])
            eff_cf = cf - fee_paid
        else:
            eff_cf = cf
            
        if i == 0:
            cum_unit = 1.0
            prev_val = val
        else:
            if prev_val > 0:
                sub_ret = (val - eff_cf) / prev_val - 1.0
                cum_unit *= (1.0 + sub_ret)
            prev_val = val
            
        twr_units.loc[dt] = cum_unit
        
    return twr_units

def calc_max_drawdown(series: pd.Series) -> float:
    """Standard maximum peak-to-trough drawdown of a valuation or TWR unit curve."""
    if series.empty:
        return 0.0
    peak = series.cummax()
    dd = (series - peak) / peak
    return float(dd.min())

def calc_custom_capital_ratio_dd(val_series: pd.Series, inv_series: pd.Series) -> float:
    """
    Custom capital ratio drawdown: decline in (Market Value / Cumulative Invested).
    This measures the worst drop in cumulative return on invested capital.
    """
    profit_ratio = val_series / inv_series
    peak = profit_ratio.cummax()
    dd = (profit_ratio - peak) / peak
    return float(dd.min())

def calc_volatility_and_sharpe(twr_units: pd.Series, 
                               rf_annual: float = 0.02, 
                               trading_days: int = 252) -> Tuple[float, float]:
    """
    Compute annualized volatility and Sharpe ratio strictly from daily returns of the TWR curve.
    This guarantees zero distortion from external deposits.
    """
    daily_rets = twr_units.pct_change().dropna()
    if len(daily_rets) < 2:
        return 0.0, np.nan
        
    rf_daily = (1.0 + rf_annual) ** (1.0 / trading_days) - 1.0
    excess_rets = daily_rets - rf_daily
    
    ann_vol = float(daily_rets.std(ddof=1) * np.sqrt(trading_days))
    if ann_vol > 1e-6:
        sharpe = float(np.sqrt(trading_days) * excess_rets.mean() / daily_rets.std(ddof=1))
    else:
        sharpe = np.nan
        
    return ann_vol, sharpe

def evaluate_portfolio(val_series: pd.Series, 
                       inv_series: pd.Series, 
                       cash_flow_dict: Dict[pd.Timestamp, float],
                       rf_annual: float = 0.02) -> Dict[str, Any]:
    """Complete institutional performance evaluation."""
    ending_val = float(val_series.iloc[-1])
    total_invested = float(inv_series.iloc[-1])
    net_profit = ending_val - total_invested
    roi = net_profit / total_invested if total_invested > 0 else 0.0
    
    # Cashflows list for XIRR
    cf_list = []
    cf_dates = []
    cf_s = pd.Series(0.0, index=val_series.index)
    for dt, amt in sorted(cash_flow_dict.items()):
        if dt in val_series.index:
            cf_list.append(-amt)
            cf_dates.append(dt)
            cf_s.loc[dt] = amt
            
    # Add final liquidating valuation
    cf_list.append(ending_val)
    cf_dates.append(val_series.index[-1])
    
    xirr = calc_xirr(cf_list, cf_dates)
    
    # TWR curve
    twr_curve = calc_twr_curve(val_series, cf_s)
    total_twr = float(twr_curve.iloc[-1] - 1.0)
    
    # Calculate annualized TWR
    days_total = (val_series.index[-1] - val_series.index[0]).days
    if days_total > 0 and twr_curve.iloc[-1] > 0:
        ann_twr = float((twr_curve.iloc[-1]) ** (365.0 / days_total) - 1.0)
    else:
        ann_twr = np.nan
        
    # Standard drawdown on TWR
    std_mdd = calc_max_drawdown(twr_curve)
    
    # Standard drawdown on market value series
    abs_mdd = calc_max_drawdown(val_series)
    
    # Custom capital-ratio drawdown
    custom_dd = calc_custom_capital_ratio_dd(val_series, inv_series)
    
    # Volatility and Sharpe
    vol, sharpe = calc_volatility_and_sharpe(twr_curve, rf_annual=rf_annual)
    
    return {
        "ending_value": ending_val,
        "total_invested": total_invested,
        "net_profit": net_profit,
        "roi": roi,
        "xirr": xirr,
        "twr_total": total_twr,
        "twr_annualized": ann_twr,
        "twr_max_drawdown": std_mdd,
        "market_val_max_drawdown": abs_mdd,
        "custom_capital_ratio_drawdown": custom_dd,
        "annualized_volatility": vol,
        "sharpe_ratio": sharpe,
        "twr_curve": twr_curve
    }

def fast_dca_xirr(monthly_rets: np.ndarray) -> float:
    """
    Fast Newton-Raphson solver for monthly DCA XIRR.
    Assumes fixed deposit at start of each month over len(monthly_rets) months.
    """
    H = len(monthly_rets)
    if H < 2:
        return np.nan
    comp = np.cumprod(1.0 + monthly_rets[::-1])[::-1]
    v_end = 10000.0 * float(np.sum(comp))
    r = 0.008  # ~10% annualized initial guess / 12
    for _ in range(15):
        discount = (1.0 + r) ** (-np.arange(H + 1))
        f_val = -10000.0 * np.sum(discount[:H]) + v_end * discount[H]
        df_val = 10000.0 * np.sum(np.arange(H) * discount[:H] / (1.0 + r)) - H * v_end * discount[H] / (1.0 + r)
        if abs(df_val) < 1e-12:
            break
        diff = f_val / df_val
        r -= diff
        if abs(diff) < 1e-7:
            break
    if not np.isfinite(r) or r <= -0.99:
        return np.nan
    return float((1.0 + r) ** 12.0 - 1.0)

def circular_block_bootstrap_median_xirr(monthly_rets: np.ndarray,
                                         h_months: int,
                                         block_length: int = 12,
                                         n_resamples: int = 1000,
                                         seed: int = 42) -> Tuple[float, float]:
    """
    Circular Block Bootstrap (Politis & Romano 1992) for median DCA XIRR.
    Resamples blocks of monthly returns to preserve macroeconomic autocorrelation,
    evaluating rolling DCA paths across reconstructed pseudo-histories.
    Returns (ci_low_95, ci_high_95) as floats rounded to 4 decimals.
    """
    T = len(monthly_rets)
    if T < h_months:
        return (np.nan, np.nan)
        
    rng = np.random.RandomState(seed)
    L = max(1, min(block_length, T))
    n_blocks = int(np.ceil(T / L))
    circ_rets = np.concatenate([monthly_rets, monthly_rets[:L]])
    
    boot_medians = []
    for _ in range(n_resamples):
        starts = rng.randint(0, T, size=n_blocks)
        blocks = [circ_rets[s:s+L] for s in starts]
        pseudo_series = np.concatenate(blocks)[:T]
        xirrs = [fast_dca_xirr(pseudo_series[i:i+h_months]) for i in range(T - h_months + 1)]
        boot_medians.append(float(np.median(xirrs)))
        
    ci_low = round(float(np.percentile(boot_medians, 2.5)), 4)
    ci_high = round(float(np.percentile(boot_medians, 97.5)), 4)
    return ci_low, ci_high

