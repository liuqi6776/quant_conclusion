# -*- coding: utf-8 -*-
"""
Master Execution & Audit Pipeline for OTC Fund Strategies
=========================================================
Runs all portfolio configurations, evaluates standard metrics, performs leave-one-out
attribution and sensitivity analyses, and exports expected_metrics.json.

Usage:
  python scripts/otc_fund/run_all.py
"""

import os
import sys
import json
import yaml
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(os.path.dirname(SCRIPT_DIR))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.instruments import CORE_FUNDS, RESEARCH_PROXIES, BENCHMARKS
from scripts.otc_fund.cashflows import build_cashflow_schedule
from scripts.otc_fund.ledger import run_chronological_simulation
from scripts.otc_fund.metrics import evaluate_portfolio, calc_max_drawdown, circular_block_bootstrap_median_xirr

DATA_PROXY_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "asset_class_proxy_panel_2015_2026.csv")
DATA_TRUE_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "fund_true_nav_panel_2015_2026.csv")
DIVIDEND_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "dividend_events.csv")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "otc_fund", "fund_dca.yaml")
EXPECTED_METRICS_PATH = os.path.join(REPO_ROOT, "configs", "otc_fund", "expected_metrics.json")

def load_data():
    if not os.path.exists(DATA_PROXY_CSV):
        raise FileNotFoundError(f"Proxy dataset not found at {DATA_PROXY_CSV}. Run build_fund_panel.py first.")
    df_proxy = pd.read_csv(DATA_PROXY_CSV, index_col=0, parse_dates=True)
    df_true = pd.read_csv(DATA_TRUE_CSV, index_col=0, parse_dates=True) if os.path.exists(DATA_TRUE_CSV) else None
    div_df = pd.read_csv(DIVIDEND_CSV, parse_dates=["date"]) if os.path.exists(DIVIDEND_CSV) else None
    return df_proxy, df_true, div_df

def compute_rolling_horizon_matrix(dates: pd.DatetimeIndex, df_proxy: pd.DataFrame, weights: dict, sub_fee: float, div_df: pd.DataFrame, rf_annual: float = 0.02) -> dict:
    """
    Compute rolling DCA return distributions across all starting months for 3Y (36m), 5Y (60m), 8Y (96m).
    Evaluates empirical P10, Median, P90, min, max, positive return ratio, and max drawdowns.
    """
    month_starts = df_proxy.resample("MS").first().index
    month_starts = [d for d in month_starts if d >= dates[0] and d <= dates[-1]]
    
    horizons = {
        "3_year": 36,
        "5_year": 60,
        "8_year": 96
    }
    
    # Precompute compounded monthly portfolio returns for Circular Block Bootstrap
    w_cols = [c for c in weights.keys() if c in df_proxy.columns]
    w_vec = np.array([weights[c] for c in w_cols])
    w_vec = w_vec / w_vec.sum()
    daily_port_rets = df_proxy[w_cols].pct_change().fillna(0.0).dot(w_vec)
    monthly_rets = (1.0 + daily_port_rets).resample("M").prod().values - 1.0

    rolling_results = {}
    for h_name, h_months in horizons.items():
        xirrs = []
        max_dds = []
        sharpes = []
        
        for i in range(len(month_starts) - h_months + 1):
            start_m = month_starts[i]
            if i + h_months < len(month_starts):
                next_m = month_starts[i + h_months]
                sub_dates = dates[(dates >= start_m) & (dates < next_m)]
            else:
                sub_dates = dates[dates >= start_m]
                
            if len(sub_dates) < h_months * 15:
                continue
                
            cfs_sub = build_cashflow_schedule(sub_dates, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")
            if len(cfs_sub) < h_months:
                continue
                
            _, df_sub = run_chronological_simulation(sub_dates, df_proxy, cfs_sub, weights, sub_fee=sub_fee, dividend_events=div_df)
            m_sub = evaluate_portfolio(df_sub["total_asset"], df_sub["cumulative_invested"], cfs_sub, rf_annual)
            
            xirrs.append(m_sub["xirr"])
            max_dds.append(m_sub["twr_max_drawdown"])
            sharpes.append(m_sub["sharpe_ratio"])
            
        if xirrs:
            # Effective independent windows (non-overlapping capacity N_eff = T / H)
            eff_indep = round(float(len(month_starts) / h_months), 1)
            
            # Circular Block Bootstrap (Politis & Romano 1992) for median XIRR (1000 resamples, block length L=12, seed 42)
            ci_low, ci_high = circular_block_bootstrap_median_xirr(
                monthly_rets, h_months=h_months, block_length=12, n_resamples=1000, seed=42
            )
            
            rolling_results[h_name] = {
                "horizon_months": h_months,
                "num_rolling_windows": len(xirrs),
                "effective_independent_windows": eff_indep,
                "median_xirr": round(float(np.median(xirrs)), 4),
                "p10_xirr": round(float(np.percentile(xirrs, 10)), 4),
                "p90_xirr": round(float(np.percentile(xirrs, 90)), 4),
                "min_xirr": round(float(np.min(xirrs)), 4),
                "max_xirr": round(float(np.max(xirrs)), 4),
                "pct_positive_xirr": round(float(np.mean(np.array(xirrs) > 0)), 4),
                "bootstrap_ci_95_median_xirr": [ci_low, ci_high],
                "median_max_drawdown": round(float(np.median(max_dds)), 4),
                "worst_max_drawdown": round(float(np.min(max_dds)), 4),
                "median_sharpe": round(float(np.median(sharpes)), 4)
            }
    return rolling_results

def run_pipeline():
    print("=" * 70)
    print("Executing Master Pipeline: OTC Fund Strategies (2015 - 2026)")
    print("=" * 70)
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    df_proxy, df_true, div_df = load_data()
    dates = df_proxy.index
    sub_fee = config["fee_model"]["subscription_fee_rate"]
    rf_annual = config["risk_free_rate_annual"]
    
    weights_9 = config["portfolios"]["canonical_9_asset"]["weights"]
    weights_7 = config["portfolios"]["modified_7_asset"]["weights"]
    
    # Pure Passive Index Portfolio Benchmark (CSI 300 + Pure Bond + Gold + Nasdaq 100 + Money Market)
    weights_passive = {
        "csi300_fund_050002": 0.20,
        "bond_pure_000015": 0.30,
        "gold_000216": 0.20,
        "nasdaq_000834": 0.20,
        "money_market_000198": 0.10
    }
    
    # Counterfactual No-Active Benchmark (Replacing 001917 -> 050002 CSI 300 10%, 017730 -> 000834 Nasdaq 100 10%)
    weights_no_active = {
        "bond_pure_000015": 0.25,
        "dividend_100032": 0.10,
        "money_market_000198": 0.10,
        "csi300_fund_050002": 0.10,
        "gold_000216": 0.20,
        "nasdaq_000834": 0.25
    }
    
    def calc_ledger_hash(df_res: pd.DataFrame) -> str:
        import hashlib
        csv_str = df_res.to_csv(lineterminator="\n", float_format="%.4f")
        return hashlib.sha256(csv_str.encode("utf-8")).hexdigest()
    
    # -------------------------------------------------------------
    # Track 1: Scenario A - 100w Lump Sum + 1w/month DCA (240.0w invested)
    # -------------------------------------------------------------
    print("\n--> Running Scenario A: 100w Lump Sum + 1w/m DCA (240.0w invested)...")
    cfs_lump = build_cashflow_schedule(dates, initial_lump=1000000.0, dca_amount=10000.0, dca_freq="monthly")
    
    # 9-asset
    _, df_res_9_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, weights_9, sub_fee=sub_fee, dividend_events=div_df)
    m_9_lump = evaluate_portfolio(df_res_9_lump["total_asset"], df_res_9_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # 7-asset
    _, df_res_7_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, weights_7, sub_fee=sub_fee, dividend_events=div_df)
    m_7_lump = evaluate_portfolio(df_res_7_lump["total_asset"], df_res_7_lump["cumulative_invested"], cfs_lump, rf_annual)
    hash_7_lump = calc_ledger_hash(df_res_7_lump)
    
    # Counterfactual No-Active Benchmark
    _, df_res_no_act_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, weights_no_active, sub_fee=sub_fee, dividend_events=div_df)
    m_no_act_lump = evaluate_portfolio(df_res_no_act_lump["total_asset"], df_res_no_act_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # Pure passive broad index benchmark
    _, df_res_pass_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, weights_passive, sub_fee=sub_fee, dividend_events=div_df)
    m_pass_lump = evaluate_portfolio(df_res_pass_lump["total_asset"], df_res_pass_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # Benchmark: SSE Composite (theoretical price index: 0 fee)
    _, df_res_sh_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, {"sh_index_000001": 1.0}, sub_fee=0.0, dividend_events=div_df)
    m_sh_lump = evaluate_portfolio(df_res_sh_lump["total_asset"], df_res_sh_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # Benchmark: CSI 300 Investable Fund (050002)
    _, df_res_300_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, {"csi300_fund_050002": 1.0}, sub_fee=sub_fee, dividend_events=div_df)
    m_300_lump = evaluate_portfolio(df_res_300_lump["total_asset"], df_res_300_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # -------------------------------------------------------------
    # Track 2: Scenario B - Pure Monthly DCA 1w/month (140.0w invested)
    # -------------------------------------------------------------
    print("--> Running Scenario B: Pure Monthly DCA (140.0w invested)...")
    cfs_dca = build_cashflow_schedule(dates, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")
    
    _, df_res_9_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, weights_9, sub_fee=sub_fee, dividend_events=div_df)
    m_9_dca = evaluate_portfolio(df_res_9_dca["total_asset"], df_res_9_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    _, df_res_7_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, weights_7, sub_fee=sub_fee, dividend_events=div_df)
    m_7_dca = evaluate_portfolio(df_res_7_dca["total_asset"], df_res_7_dca["cumulative_invested"], cfs_dca, rf_annual)
    hash_7_dca = calc_ledger_hash(df_res_7_dca)
    
    # Counterfactual No-Active Benchmark
    _, df_res_no_act_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, weights_no_active, sub_fee=sub_fee, dividend_events=div_df)
    m_no_act_dca = evaluate_portfolio(df_res_no_act_dca["total_asset"], df_res_no_act_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    _, df_res_pass_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, weights_passive, sub_fee=sub_fee, dividend_events=div_df)
    m_pass_dca = evaluate_portfolio(df_res_pass_dca["total_asset"], df_res_pass_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    _, df_res_sh_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, {"sh_index_000001": 1.0}, sub_fee=0.0, dividend_events=div_df)
    m_sh_dca = evaluate_portfolio(df_res_sh_dca["total_asset"], df_res_sh_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    _, df_res_300_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, {"csi300_fund_050002": 1.0}, sub_fee=sub_fee, dividend_events=div_df)
    m_300_dca = evaluate_portfolio(df_res_300_dca["total_asset"], df_res_300_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    # -------------------------------------------------------------
    # Track 3: Scenario C - Weekly 3,150 RMB DCA Sensitivity Track
    # -------------------------------------------------------------
    print("--> Running Scenario C: Weekly 3,150 RMB DCA Sensitivity Track...")
    cfs_weekly = build_cashflow_schedule(dates, initial_lump=0.0, dca_amount=3150.0, dca_freq="weekly")
    _, df_res_7_weekly = run_chronological_simulation(dates, df_proxy, cfs_weekly, weights_7, sub_fee=sub_fee, dividend_events=div_df)
    m_7_weekly = evaluate_portfolio(df_res_7_weekly["total_asset"], df_res_7_weekly["cumulative_invested"], cfs_weekly, rf_annual)

    # -------------------------------------------------------------
    # Track 4: Real Fund Common Window (2023-02-09 to 2026-08-06)
    # -------------------------------------------------------------
    print("--> Running Scenario D: Real Fund Common Inception Window (2023-2026)...")
    dates_common = dates[dates >= pd.Timestamp("2023-02-09")]
    cfs_common = build_cashflow_schedule(dates_common, initial_lump=1000000.0, dca_amount=10000.0, dca_freq="monthly")
    
    true_weights_9 = {
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
    _, df_res_common_9 = run_chronological_simulation(dates_common, df_true, cfs_common, true_weights_9, sub_fee=sub_fee, dividend_events=div_df)
    m_common_9 = evaluate_portfolio(df_res_common_9["total_asset"], df_res_common_9["cumulative_invested"], cfs_common, rf_annual)

    # -------------------------------------------------------------
    # Track 5: Start-Date Sensitivity (2015, 2016, 2018, 2021)
    # -------------------------------------------------------------
    print("--> Running Start-Date Sensitivity Analysis...")
    start_date_results = {}
    for label, start_s in [
        ("2015_bubble_peak_crash", "2015-01-05"),
        ("2016_circuit_breaker_bottom", "2016-01-04"),
        ("2018_trade_war_peak", "2018-01-02"),
        ("2021_pre_tightening_peak", "2021-01-04")
    ]:
        sub_d = dates[dates >= pd.Timestamp(start_s)]
        cfs_sub = build_cashflow_schedule(sub_d, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")
        _, df_s7 = run_chronological_simulation(sub_d, df_proxy, cfs_sub, weights_7, sub_fee=sub_fee, dividend_events=div_df)
        m_s7 = evaluate_portfolio(df_s7["total_asset"], df_s7["cumulative_invested"], cfs_sub, rf_annual)
        
        _, df_spass = run_chronological_simulation(sub_d, df_proxy, cfs_sub, weights_passive, sub_fee=sub_fee, dividend_events=div_df)
        m_spass = evaluate_portfolio(df_spass["total_asset"], df_spass["cumulative_invested"], cfs_sub, rf_annual)
        
        _, df_ssh = run_chronological_simulation(sub_d, df_proxy, cfs_sub, {"sh_index_000001": 1.0}, sub_fee=0.0, dividend_events=div_df)
        m_ssh = evaluate_portfolio(df_ssh["total_asset"], df_ssh["cumulative_invested"], cfs_sub, rf_annual)
        
        start_date_results[label] = {
            "start_date": start_s,
            "invested_total": m_s7["total_invested"],
            "modified_7_asset": {
                "ending_value": round(m_s7["ending_value"], 2),
                "xirr": round(m_s7["xirr"], 4),
                "twr_max_drawdown": round(m_s7["twr_max_drawdown"], 4)
            },
            "passive_broad_index": {
                "ending_value": round(m_spass["ending_value"], 2),
                "xirr": round(m_spass["xirr"], 4),
                "twr_max_drawdown": round(m_spass["twr_max_drawdown"], 4)
            },
            "shanghai_index": {
                "ending_value": round(m_ssh["ending_value"], 2),
                "xirr": round(m_ssh["xirr"], 4),
                "twr_max_drawdown": round(m_ssh["twr_max_drawdown"], 4)
            }
        }

    # -------------------------------------------------------------
    # Track 6: In-Sample (2015-2020) vs Out-of-Sample (2021-2026) Split
    # -------------------------------------------------------------
    print("--> Running In-Sample vs Out-of-Sample Split Analysis...")
    d_is = dates[(dates >= "2015-01-05") & (dates <= "2020-12-31")]
    d_oos = dates[(dates >= "2021-01-04") & (dates <= "2026-08-06")]
    
    cfs_is = build_cashflow_schedule(d_is, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")
    _, df_is_7 = run_chronological_simulation(d_is, df_proxy, cfs_is, weights_7, sub_fee=sub_fee, dividend_events=div_df)
    m_is_7 = evaluate_portfolio(df_is_7["total_asset"], df_is_7["cumulative_invested"], cfs_is, rf_annual)
    
    _, df_is_pass = run_chronological_simulation(d_is, df_proxy, cfs_is, weights_passive, sub_fee=sub_fee, dividend_events=div_df)
    m_is_pass = evaluate_portfolio(df_is_pass["total_asset"], df_is_pass["cumulative_invested"], cfs_is, rf_annual)
    
    _, df_is_sh = run_chronological_simulation(d_is, df_proxy, cfs_is, {"sh_index_000001": 1.0}, sub_fee=0.0, dividend_events=div_df)
    m_is_sh = evaluate_portfolio(df_is_sh["total_asset"], df_is_sh["cumulative_invested"], cfs_is, rf_annual)
    
    cfs_oos = build_cashflow_schedule(d_oos, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")
    _, df_oos_7 = run_chronological_simulation(d_oos, df_proxy, cfs_oos, weights_7, sub_fee=sub_fee, dividend_events=div_df)
    m_oos_7 = evaluate_portfolio(df_oos_7["total_asset"], df_oos_7["cumulative_invested"], cfs_oos, rf_annual)
    
    _, df_oos_pass = run_chronological_simulation(d_oos, df_proxy, cfs_oos, weights_passive, sub_fee=sub_fee, dividend_events=div_df)
    m_oos_pass = evaluate_portfolio(df_oos_pass["total_asset"], df_oos_pass["cumulative_invested"], cfs_oos, rf_annual)
    
    _, df_oos_sh = run_chronological_simulation(d_oos, df_proxy, cfs_oos, {"sh_index_000001": 1.0}, sub_fee=0.0, dividend_events=div_df)
    m_oos_sh = evaluate_portfolio(df_oos_sh["total_asset"], df_oos_sh["cumulative_invested"], cfs_oos, rf_annual)
    
    split_results = {
        "in_sample_2015_2020": {
            "window": "2015-01-05 to 2020-12-31",
            "months": len(cfs_is),
            "invested_total": m_is_7["total_invested"],
            "modified_7_asset": {"ending_value": round(m_is_7["ending_value"], 2), "xirr": round(m_is_7["xirr"], 4), "twr_max_drawdown": round(m_is_7["twr_max_drawdown"], 4)},
            "passive_broad_index": {"ending_value": round(m_is_pass["ending_value"], 2), "xirr": round(m_is_pass["xirr"], 4), "twr_max_drawdown": round(m_is_pass["twr_max_drawdown"], 4)},
            "shanghai_index": {"ending_value": round(m_is_sh["ending_value"], 2), "xirr": round(m_is_sh["xirr"], 4), "twr_max_drawdown": round(m_is_sh["twr_max_drawdown"], 4)}
        },
        "out_of_sample_2021_2026": {
            "window": "2021-01-04 to 2026-08-06",
            "months": len(cfs_oos),
            "invested_total": m_oos_7["total_invested"],
            "modified_7_asset": {"ending_value": round(m_oos_7["ending_value"], 2), "xirr": round(m_oos_7["xirr"], 4), "twr_max_drawdown": round(m_oos_7["twr_max_drawdown"], 4)},
            "passive_broad_index": {"ending_value": round(m_oos_pass["ending_value"], 2), "xirr": round(m_oos_pass["xirr"], 4), "twr_max_drawdown": round(m_oos_pass["twr_max_drawdown"], 4)},
            "shanghai_index": {"ending_value": round(m_oos_sh["ending_value"], 2), "xirr": round(m_oos_sh["xirr"], 4), "twr_max_drawdown": round(m_oos_sh["twr_max_drawdown"], 4)}
        }
    }

    # -------------------------------------------------------------
    # Robustness: Leave-One-Out Asset Attribution (Scenario B Pure DCA)
    # -------------------------------------------------------------
    print("--> Running Leave-One-Out Asset Sensitivity Attribution...")
    loo_results = {}
    for dropped_asset in weights_9.keys():
        sub_weights = {k: v for k, v in weights_9.items() if k != dropped_asset}
        tot_w = sum(sub_weights.values())
        norm_weights = {k: v / tot_w for k, v in sub_weights.items()}
        _, df_loo = run_chronological_simulation(dates, df_proxy, cfs_dca, norm_weights, sub_fee=sub_fee, dividend_events=div_df)
        m_loo = evaluate_portfolio(df_loo["total_asset"], df_loo["cumulative_invested"], cfs_dca, rf_annual)
        loo_results[dropped_asset] = {
            "ending_value": round(m_loo["ending_value"], 2),
            "xirr": round(m_loo["xirr"], 4),
            "twr_max_drawdown": round(m_loo["twr_max_drawdown"], 4)
        }

    # -------------------------------------------------------------
    # Track 7: Rolling Horizon Distribution Matrix (3Y, 5Y, 8Y DCA)
    # -------------------------------------------------------------
    print("--> Running Rolling Horizon Matrix (3Y, 5Y, 8Y DCA)...")
    rolling_matrix_7 = compute_rolling_horizon_matrix(dates, df_proxy, weights_7, sub_fee, div_df, rf_annual)

    # -------------------------------------------------------------
    # Track 8: Target Volatility 7% Risk Budgeting Experiment
    # -------------------------------------------------------------
    print("--> Running Target Volatility 7% Experiment (Open-Loop vs Proportional Control)...")
    from scripts.otc_fund.vol_target import run_vol_target_simulation
    vt_weights = {
        "bond_pure_000015": 0.40,
        "dividend_100032": 0.20,
        "gold_000216": 0.15,
        "nasdaq_000834": 0.15,
        "csi300_fund_050002": 0.10
    }
    led_ol, df_ol, diag_ol = run_vol_target_simulation(
        dates, df_proxy, cfs_lump, vt_weights, mode="open_loop", return_diagnostics=True
    )
    res_ol = evaluate_portfolio(df_ol["total_asset"], df_ol["cumulative_invested"], cfs_lump, rf_annual)

    led_pc, df_pc, diag_pc = run_vol_target_simulation(
        dates, df_proxy, cfs_lump, vt_weights, mode="proportional_control", kp=0.25, return_diagnostics=True
    )
    res_pc = evaluate_portfolio(df_pc["total_asset"], df_pc["cumulative_invested"], cfs_lump, rf_annual)

    # -------------------------------------------------------------
    # Track 9: Walk-Forward Dynamic Risk Parity Simulation
    # -------------------------------------------------------------
    print("--> Running Walk-Forward Dynamic Risk Parity Simulation...")
    from scripts.otc_fund.walk_forward import compute_walk_forward_weights
    wf_risk_assets = ["bond_pure_000015", "dividend_100032", "proxy_quant_a", "gold_000216", "nasdaq_000834", "proxy_global_tech"]
    wf_table, wf_sched_weights = compute_walk_forward_weights(
        df_proxy, wf_risk_assets, initial_weights=weights_7, train_months=36, step_months=12
    )
    led_wf, df_wf = run_chronological_simulation(dates, df_proxy, cfs_dca, wf_sched_weights)
    res_wf_full = evaluate_portfolio(df_wf["total_asset"], df_wf["cumulative_invested"], cfs_dca, rf_annual)

    dates_oos = dates[dates >= pd.Timestamp("2018-01-02")]
    cfs_oos = build_cashflow_schedule(dates_oos, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")
    led_wf_oos, df_wf_oos = run_chronological_simulation(dates_oos, df_proxy, cfs_oos, wf_sched_weights)
    res_wf_oos = evaluate_portfolio(df_wf_oos["total_asset"], df_wf_oos["cumulative_invested"], cfs_oos, rf_annual)

    # Format JSON payload
    clean_metrics = {
        "version": "2.2.0",
        "generated_at": pd.Timestamp.now().isoformat(),
        "notes": "Verified baseline metrics generated by run_all.py with explicit dividend reinvestment, zero cash fee, and rolling horizon distributions",
        "scenarios": {
            "lump_100w_plus_monthly_1w": {
                "invested_total": m_9_lump["total_invested"],
                "canonical_9_asset": {
                    "ending_value": round(m_9_lump["ending_value"], 2),
                    "net_profit": round(m_9_lump["net_profit"], 2),
                    "roi": round(m_9_lump["roi"], 4),
                    "xirr": round(m_9_lump["xirr"], 4),
                    "twr_total": round(m_9_lump["twr_total"], 4),
                    "twr_annualized": round(m_9_lump["twr_annualized"], 4),
                    "twr_max_drawdown": round(m_9_lump["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_9_lump["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_9_lump["sharpe_ratio"], 4)
                },
                "modified_7_asset": {
                    "ending_value": round(m_7_lump["ending_value"], 2),
                    "net_profit": round(m_7_lump["net_profit"], 2),
                    "roi": round(m_7_lump["roi"], 4),
                    "xirr": round(m_7_lump["xirr"], 4),
                    "twr_total": round(m_7_lump["twr_total"], 4),
                    "twr_annualized": round(m_7_lump["twr_annualized"], 4),
                    "twr_max_drawdown": round(m_7_lump["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_7_lump["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_7_lump["sharpe_ratio"], 4),
                    "ledger_hash": hash_7_lump
                },
                "counterfactual_no_active": {
                    "ending_value": round(m_no_act_lump["ending_value"], 2),
                    "net_profit": round(m_no_act_lump["net_profit"], 2),
                    "roi": round(m_no_act_lump["roi"], 4),
                    "xirr": round(m_no_act_lump["xirr"], 4),
                    "twr_max_drawdown": round(m_no_act_lump["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_no_act_lump["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_no_act_lump["sharpe_ratio"], 4)
                },
                "passive_broad_index": {
                    "ending_value": round(m_pass_lump["ending_value"], 2),
                    "net_profit": round(m_pass_lump["net_profit"], 2),
                    "roi": round(m_pass_lump["roi"], 4),
                    "xirr": round(m_pass_lump["xirr"], 4),
                    "twr_max_drawdown": round(m_pass_lump["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_pass_lump["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_pass_lump["sharpe_ratio"], 4)
                },
                "shanghai_index": {
                    "ending_value": round(m_sh_lump["ending_value"], 2),
                    "net_profit": round(m_sh_lump["net_profit"], 2),
                    "roi": round(m_sh_lump["roi"], 4),
                    "xirr": round(m_sh_lump["xirr"], 4),
                    "twr_max_drawdown": round(m_sh_lump["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_sh_lump["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_sh_lump["sharpe_ratio"], 4)
                },
                "csi300_fund": {
                    "ending_value": round(m_300_lump["ending_value"], 2),
                    "net_profit": round(m_300_lump["net_profit"], 2),
                    "roi": round(m_300_lump["roi"], 4),
                    "xirr": round(m_300_lump["xirr"], 4),
                    "twr_max_drawdown": round(m_300_lump["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_300_lump["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_300_lump["sharpe_ratio"], 4)
                }
            },
            "pure_monthly_1w_dca": {
                "invested_total": m_9_dca["total_invested"],
                "canonical_9_asset": {
                    "ending_value": round(m_9_dca["ending_value"], 2),
                    "net_profit": round(m_9_dca["net_profit"], 2),
                    "roi": round(m_9_dca["roi"], 4),
                    "xirr": round(m_9_dca["xirr"], 4),
                    "twr_total": round(m_9_dca["twr_total"], 4),
                    "twr_annualized": round(m_9_dca["twr_annualized"], 4),
                    "twr_max_drawdown": round(m_9_dca["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_9_dca["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_9_dca["sharpe_ratio"], 4)
                },
                "modified_7_asset": {
                    "ending_value": round(m_7_dca["ending_value"], 2),
                    "net_profit": round(m_7_dca["net_profit"], 2),
                    "roi": round(m_7_dca["roi"], 4),
                    "xirr": round(m_7_dca["xirr"], 4),
                    "twr_total": round(m_7_dca["twr_total"], 4),
                    "twr_annualized": round(m_7_dca["twr_annualized"], 4),
                    "twr_max_drawdown": round(m_7_dca["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_7_dca["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_7_dca["sharpe_ratio"], 4),
                    "ledger_hash": hash_7_dca
                },
                "counterfactual_no_active": {
                    "ending_value": round(m_no_act_dca["ending_value"], 2),
                    "net_profit": round(m_no_act_dca["net_profit"], 2),
                    "roi": round(m_no_act_dca["roi"], 4),
                    "xirr": round(m_no_act_dca["xirr"], 4),
                    "twr_max_drawdown": round(m_no_act_dca["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_no_act_dca["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_no_act_dca["sharpe_ratio"], 4)
                },
                "passive_broad_index": {
                    "ending_value": round(m_pass_dca["ending_value"], 2),
                    "net_profit": round(m_pass_dca["net_profit"], 2),
                    "roi": round(m_pass_dca["roi"], 4),
                    "xirr": round(m_pass_dca["xirr"], 4),
                    "twr_max_drawdown": round(m_pass_dca["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_pass_dca["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_pass_dca["sharpe_ratio"], 4)
                },
                "shanghai_index": {
                    "ending_value": round(m_sh_dca["ending_value"], 2),
                    "net_profit": round(m_sh_dca["net_profit"], 2),
                    "roi": round(m_sh_dca["roi"], 4),
                    "xirr": round(m_sh_dca["xirr"], 4),
                    "twr_max_drawdown": round(m_sh_dca["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_sh_dca["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_sh_dca["sharpe_ratio"], 4)
                },
                "csi300_fund": {
                    "ending_value": round(m_300_dca["ending_value"], 2),
                    "net_profit": round(m_300_dca["net_profit"], 2),
                    "roi": round(m_300_dca["roi"], 4),
                    "xirr": round(m_300_dca["xirr"], 4),
                    "twr_max_drawdown": round(m_300_dca["twr_max_drawdown"], 4),
                    "custom_capital_ratio_drawdown": round(m_300_dca["custom_capital_ratio_drawdown"], 4),
                    "sharpe_ratio": round(m_300_dca["sharpe_ratio"], 4)
                }
            },
            "weekly_3150_dca": {
                "invested_total": m_7_weekly["total_invested"],
                "ending_value": round(m_7_weekly["ending_value"], 2),
                "roi": round(m_7_weekly["roi"], 4),
                "xirr": round(m_7_weekly["xirr"], 4),
                "twr_max_drawdown": round(m_7_weekly["twr_max_drawdown"], 4)
            },
            "real_fund_common_window_2023_2026": {
                "window": "2023-02-09 to 2026-08-06",
                "invested_total": m_common_9["total_invested"],
                "ending_value": round(m_common_9["ending_value"], 2),
                "xirr": round(m_common_9["xirr"], 4),
                "twr_max_drawdown": round(m_common_9["twr_max_drawdown"], 4),
                "sharpe_ratio": round(m_common_9["sharpe_ratio"], 4)
            },
            "start_date_sensitivity": start_date_results,
            "sample_split": split_results,
            "leave_one_out_sensitivity": loo_results,
            "rolling_horizon_matrix": rolling_matrix_7,
            "vol_target_proportional_control_experiment": {
                "invested_total": res_ol["total_invested"],
                "description": "100w lump sum + 1w/m DCA, 40% bond + 20% dividend + 15% gold + 15% nasdaq + 10% csi300",
                "open_loop": {
                    "ending_value": round(res_ol["ending_value"], 2),
                    "xirr": round(res_ol["xirr"], 4),
                    "realized_vol": round(diag_ol["realized_vol"], 4),
                    "vol_tracking_error": round(diag_ol["vol_tracking_error"], 4),
                    "multiplier_churn": round(diag_ol["multiplier_churn"], 2),
                    "red_fees_paid": round(diag_ol["red_fees_paid"], 2),
                    "sharpe_ratio": round(diag_ol["sharpe_ratio"], 4)
                },
                "proportional_control_kp_025": {
                    "ending_value": round(res_pc["ending_value"], 2),
                    "xirr": round(res_pc["xirr"], 4),
                    "realized_vol": round(diag_pc["realized_vol"], 4),
                    "vol_tracking_error": round(diag_pc["vol_tracking_error"], 4),
                    "multiplier_churn": round(diag_pc["multiplier_churn"], 2),
                    "red_fees_paid": round(diag_pc["red_fees_paid"], 2),
                    "sharpe_ratio": round(diag_pc["sharpe_ratio"], 4)
                }
            },
            "walk_forward_dynamic_risk_parity": {
                "full_period_2015_2026": {
                    "invested_total": res_wf_full["total_invested"],
                    "ending_value": round(res_wf_full["ending_value"], 2),
                    "xirr": round(res_wf_full["xirr"], 4),
                    "twr_max_drawdown": round(res_wf_full["twr_max_drawdown"], 4),
                    "sharpe_ratio": round(res_wf_full["sharpe_ratio"], 4)
                },
                "pure_oos_2018_2026": {
                    "invested_total": res_wf_oos["total_invested"],
                    "ending_value": round(res_wf_oos["ending_value"], 2),
                    "xirr": round(res_wf_oos["xirr"], 4),
                    "twr_max_drawdown": round(res_wf_oos["twr_max_drawdown"], 4),
                    "sharpe_ratio": round(res_wf_oos["sharpe_ratio"], 4)
                }
            }
        },
        "metrics_tolerances": {
            "xirr_tolerance": 0.005,
            "ending_val_rel_tolerance": 0.01,
            "max_drawdown_tolerance": 0.01
        }
    }
    
    with open(EXPECTED_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(clean_metrics, f, ensure_ascii=False, indent=2)
    print(f"\n[OK] Exported expected metrics to {EXPECTED_METRICS_PATH}")
    
    print("\n" + "=" * 70)
    print("KEY REVENUE & RISK AUDIT RESULTS SUMMARY (DIVIDEND-REINVESTED)")
    print("=" * 70)
    print(f"1. Scenario A (100w + 1w/m DCA, Total {m_7_lump['total_invested']/10000:.1f}w invested):")
    print(f"   - Canonical 9-Asset: Ending {m_9_lump['ending_value']/10000:.2f}w, XIRR {m_9_lump['xirr']*100:.2f}%, TWR MaxDD {m_9_lump['twr_max_drawdown']*100:.2f}%, Sharpe {m_9_lump['sharpe_ratio']:.2f}")
    print(f"   - Modified 7-Asset : Ending {m_7_lump['ending_value']/10000:.2f}w, XIRR {m_7_lump['xirr']*100:.2f}%, TWR MaxDD {m_7_lump['twr_max_drawdown']*100:.2f}%, Sharpe {m_7_lump['sharpe_ratio']:.2f}")
    print(f"   - Passive Broad Idx: Ending {m_pass_lump['ending_value']/10000:.2f}w, XIRR {m_pass_lump['xirr']*100:.2f}%, TWR MaxDD {m_pass_lump['twr_max_drawdown']*100:.2f}%, Sharpe {m_pass_lump['sharpe_ratio']:.2f}")
    print(f"   - SSE Composite    : Ending {m_sh_lump['ending_value']/10000:.2f}w, XIRR {m_sh_lump['xirr']*100:.2f}%, TWR MaxDD {m_sh_lump['twr_max_drawdown']*100:.2f}%")
    print(f"2. Scenario B (Pure Monthly 1w DCA, Total {m_7_dca['total_invested']/10000:.1f}w invested):")
    print(f"   - Canonical 9-Asset: Ending {m_9_dca['ending_value']/10000:.2f}w, XIRR {m_9_dca['xirr']*100:.2f}%, Custom Profit DD {m_9_dca['custom_capital_ratio_drawdown']*100:.2f}%")
    print(f"   - Modified 7-Asset : Ending {m_7_dca['ending_value']/10000:.2f}w, XIRR {m_7_dca['xirr']*100:.2f}%, Custom Profit DD {m_7_dca['custom_capital_ratio_drawdown']*100:.2f}%")
    print(f"   - Passive Broad Idx: Ending {m_pass_dca['ending_value']/10000:.2f}w, XIRR {m_pass_dca['xirr']*100:.2f}%, Custom Profit DD {m_pass_dca['custom_capital_ratio_drawdown']*100:.2f}%")
    print(f"   - SSE Composite    : Ending {m_sh_dca['ending_value']/10000:.2f}w, XIRR {m_sh_dca['xirr']*100:.2f}%, Custom Profit DD {m_sh_dca['custom_capital_ratio_drawdown']*100:.2f}%")
    print(f"3. Real Fund Common Window (2023-2026, all 9 funds exist in reality):")
    print(f"   - True 9-Asset     : Ending {m_common_9['ending_value']/10000:.2f}w, XIRR {m_common_9['xirr']*100:.2f}%, Sharpe {m_common_9['sharpe_ratio']:.2f}")
    print(f"4. Rolling Horizon Distributions (Modified 7-Asset):")
    for k, v in rolling_matrix_7.items():
        print(f"   - {k} ({v['num_rolling_windows']} windows): Median XIRR {v['median_xirr']*100:.2f}%, P10-P90 [{v['p10_xirr']*100:.2f}% - {v['p90_xirr']*100:.2f}%], Worst DD {v['worst_max_drawdown']*100:.2f}%")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()
