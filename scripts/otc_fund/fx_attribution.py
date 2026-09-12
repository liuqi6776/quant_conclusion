# -*- coding: utf-8 -*-
"""
QDII Foreign Exchange Exposure Modeling & Return Attribution Engine
===================================================================
Rigorous quantitative decomposition of foreign asset returns denominated in CNY.

Mathematical Framework:
-----------------------
1. Daily Return Compound Identity:
   1 + R_t^{CNY} = (1 + R_t^{USD}) * (1 + R_t^{FX})
   => R_t^{USD} = (1 + R_t^{CNY}) / (1 + R_t^{FX}) - 1

2. Cumulative Return Exact 3-Way Additive Decomposition:
   1 + R_{cum}^{CNY} = (1 + R_{cum}^{USD}) * (1 + R_{cum}^{FX})
   => R_{cum}^{CNY} = R_{cum}^{USD} + R_{cum}^{FX} + (R_{cum}^{USD} * R_{cum}^{FX})
   where:
   - R_{cum}^{USD}: Pure foreign underlying asset performance (e.g. US tech beta)
   - R_{cum}^{FX}: Currency movement (USD appreciation against CNY)
   - Interaction: Cross-product compounding term

3. Annualized Log-CAGR Additive Share:
   ln(1 + g_{CNY}) = ln(1 + g_{USD}) + ln(1 + g_{FX})
   - USD Asset Share = ln(1 + g_{USD}) / ln(1 + g_{CNY})
   - FX Tailwind Share = ln(1 + g_{FX}) / ln(1 + g_{CNY})
"""

import os
import sys
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_FX_PATH = os.path.join(REPO_ROOT, "data", "otc_fund", "usd_cny_daily_2015_2026.csv")
DEFAULT_PANEL_PATH = os.path.join(REPO_ROOT, "data", "otc_fund", "fund_dca_daily_panel_2015_2026.csv")

def load_fx_series(filepath: Optional[str] = None) -> pd.Series:
    """Load standardized daily USD/CNY exchange rate series."""
    path = filepath or DEFAULT_FX_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(f"USD/CNY series not found at: {path}")
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df["usd_cny"].astype(float).sort_index()

def decompose_qdii_return(cny_nav_series: pd.Series, fx_series: pd.Series) -> Dict[str, Any]:
    """
    Perform exact 3-way return decomposition on a CNY-denominated QDII NAV series.
    """
    clean_cny = cny_nav_series.dropna().sort_index()
    common_idx = clean_cny.index.intersection(fx_series.index)
    
    if len(common_idx) < 2:
        raise ValueError("Insufficient overlapping dates between NAV series and FX series.")
        
    s_cny = clean_cny.loc[common_idx]
    s_fx = fx_series.loc[common_idx]
    
    cny_0, cny_T = s_cny.iloc[0], s_cny.iloc[-1]
    fx_0, fx_T = s_fx.iloc[0], s_fx.iloc[-1]
    
    r_cny = float(cny_T / cny_0 - 1.0)
    r_fx = float(fx_T / fx_0 - 1.0)
    r_usd = float((1.0 + r_cny) / (1.0 + r_fx) - 1.0)
    interaction = float(r_usd * r_fx)
    
    days = (common_idx[-1] - common_idx[0]).days
    years = days / 365.25
    
    cagr_cny = float((1.0 + r_cny) ** (1.0 / years) - 1.0) if years > 0 else np.nan
    cagr_usd = float((1.0 + r_usd) ** (1.0 / years) - 1.0) if years > 0 else np.nan
    cagr_fx = float((1.0 + r_fx) ** (1.0 / years) - 1.0) if years > 0 else np.nan
    
    log_cny = float(np.log(1.0 + cagr_cny)) if cagr_cny > -1 else np.nan
    log_usd = float(np.log(1.0 + cagr_usd)) if cagr_usd > -1 else np.nan
    log_fx = float(np.log(1.0 + cagr_fx)) if cagr_fx > -1 else np.nan
    
    usd_share = float(log_usd / log_cny) if (log_cny and abs(log_cny) > 1e-6) else np.nan
    fx_share = float(log_fx / log_cny) if (log_cny and abs(log_cny) > 1e-6) else np.nan
    
    return {
        "start_date": common_idx[0].strftime("%Y-%m-%d"),
        "end_date": common_idx[-1].strftime("%Y-%m-%d"),
        "calendar_days": days,
        "years": round(years, 2),
        "cny_start": cny_0,
        "cny_end": cny_T,
        "fx_start": fx_0,
        "fx_end": fx_T,
        "return_cny": r_cny,
        "return_usd": r_usd,
        "return_fx": r_fx,
        "interaction": interaction,
        "identity_reconciled": bool(abs(r_usd + r_fx + interaction - r_cny) < 1e-10),
        "cagr_cny": cagr_cny,
        "cagr_usd": cagr_usd,
        "cagr_fx": cagr_fx,
        "log_additive_share_usd": usd_share,
        "log_additive_share_fx": fx_share
    }

def compute_yearly_attribution_table(cny_nav_series: pd.Series, fx_series: pd.Series) -> pd.DataFrame:
    """
    Compute annual breakdown of returns into USD asset, FX movement, and interaction.
    """
    clean_cny = cny_nav_series.dropna().sort_index()
    common_idx = clean_cny.index.intersection(fx_series.index)
    
    s_cny = clean_cny.loc[common_idx]
    s_fx = fx_series.loc[common_idx]
    
    daily_df = pd.DataFrame({"cny": s_cny, "fx": s_fx}, index=common_idx)
    daily_df["r_cny"] = daily_df["cny"].pct_change()
    daily_df["r_fx"] = daily_df["fx"].pct_change()
    daily_df["r_usd"] = (1.0 + daily_df["r_cny"]) / (1.0 + daily_df["r_fx"]) - 1.0
    
    records = []
    for yr, grp in daily_df.groupby(daily_df.index.year):
        y_cny = float((1.0 + grp["r_cny"]).prod() - 1.0)
        y_fx = float((1.0 + grp["r_fx"]).prod() - 1.0)
        y_usd = float((1.0 + grp["r_usd"]).prod() - 1.0)
        y_inter = float(y_cny - (y_usd + y_fx))
        records.append({
            "year": yr,
            "cny_return": y_cny,
            "usd_asset_return": y_usd,
            "fx_currency_return": y_fx,
            "interaction": y_inter
        })
        
    return pd.DataFrame(records)

def simulate_fx_reversal_stress(current_cny_nav: float,
                                fx_shocks: Optional[List[float]] = None) -> pd.DataFrame:
    """
    Stress-test portfolio or QDII fund under RMB appreciation shocks.
    fx_shocks: List of FX changes (e.g. [-0.05, -0.10, -0.15] for 5%, 10%, 15% RMB appreciation).
    """
    shocks = fx_shocks or [-0.05, -0.10, -0.15, -0.20]
    records = []
    for shock in shocks:
        stressed_nav = current_cny_nav * (1.0 + shock)
        records.append({
            "rmb_appreciation_shock": f"{abs(shock)*100:.1f}%",
            "fx_return": shock,
            "stressed_nav": stressed_nav,
            "nav_drag_cny": stressed_nav - current_cny_nav,
            "pct_loss_from_fx": shock
        })
    return pd.DataFrame(records)

if __name__ == "__main__":
    fx = load_fx_series()
    panel = pd.read_csv(DEFAULT_PANEL_PATH, index_col=0, parse_dates=True)
    
    if "nasdaq_000834" in panel.columns:
        print("=================================================================")
        print("   QDII RETURN ATTRIBUTION: 000834 大成纳斯达克100A (2015-2026)")
        print("=================================================================")
        res = decompose_qdii_return(panel["nasdaq_000834"], fx)
        print(f"Window: {res['start_date']} -> {res['end_date']} ({res['years']} years)")
        print(f"USD/CNY Central Parity: {res['fx_start']:.4f} -> {res['fx_end']:.4f} ({res['return_fx']*100:+.2f}%)")
        print(f"Cumulative CNY Return:  {res['return_cny']*100:+.2f}%")
        print(f"Cumulative USD Return:  {res['return_usd']*100:+.2f}%")
        print(f"Compounding Interaction:{res['interaction']*100:+.2f}%")
        print(f"Additive Identity Check: {'PASS' if res['identity_reconciled'] else 'FAIL'}")
        print("\nAnnualized Growth (CAGR):")
        print(f"  CNY CAGR: {res['cagr_cny']*100:.2f}%")
        print(f"  USD CAGR: {res['cagr_usd']*100:.2f}%")
        print(f"  FX CAGR:  {res['cagr_fx']*100:.2f}%")
        print(f"Log Additive Share: US Asset = {res['log_additive_share_usd']*100:.1f}%, Currency Tailwind = {res['log_additive_share_fx']*100:.1f}%")
        
        print("\nYearly Return Attribution Table:")
        df_y = compute_yearly_attribution_table(panel["nasdaq_000834"], fx)
        print(df_y.to_string(index=False, formatters={
            "cny_return": lambda x: f"{x*100:+.2f}%",
            "usd_asset_return": lambda x: f"{x*100:+.2f}%",
            "fx_currency_return": lambda x: f"{x*100:+.2f}%",
            "interaction": lambda x: f"{x*100:+.2f}%"
        }))
