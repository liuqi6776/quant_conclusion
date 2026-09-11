# -*- coding: utf-8 -*-
"""
Master Execution & Audit Pipeline for OTC Fund Strategies
=========================================================
Runs all portfolio configurations, evaluates standard metrics, performs leave-one-out
attribution and rolling analyses, and exports expected_metrics.json.

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
from scripts.otc_fund.cashflows import build_cashflow_schedule, generate_monthly_dca_dates
from scripts.otc_fund.ledger import run_chronological_simulation
from scripts.otc_fund.metrics import evaluate_portfolio, calc_max_drawdown

DATA_PROXY_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "asset_class_proxy_panel_2015_2026.csv")
DATA_TRUE_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "fund_true_nav_panel_2015_2026.csv")
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "otc_fund", "fund_dca.yaml")
EXPECTED_METRICS_PATH = os.path.join(REPO_ROOT, "configs", "otc_fund", "expected_metrics.json")

def load_data():
    if not os.path.exists(DATA_PROXY_CSV):
        raise FileNotFoundError(f"Proxy dataset not found at {DATA_PROXY_CSV}. Run build_fund_panel.py first.")
    df_proxy = pd.read_csv(DATA_PROXY_CSV, index_col=0, parse_dates=True)
    df_true = pd.read_csv(DATA_TRUE_CSV, index_col=0, parse_dates=True) if os.path.exists(DATA_TRUE_CSV) else None
    return df_proxy, df_true

def run_pipeline():
    print("=" * 70)
    print("Executing Master Pipeline: OTC Fund Strategies (2015 - 2026)")
    print("=" * 70)
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    df_proxy, df_true = load_data()
    dates = df_proxy.index
    sub_fee = config["fee_model"]["subscription_fee_rate"]
    rf_annual = config["risk_free_rate_annual"]
    
    weights_9 = config["portfolios"]["canonical_9_asset"]["weights"]
    weights_7 = config["portfolios"]["modified_7_asset"]["weights"]
    
    results = {}
    
    # -------------------------------------------------------------
    # Track 1: Scenario A - 100w Lump Sum + 1w/month DCA (2015-2026)
    # -------------------------------------------------------------
    print("\n--> Running Scenario A: 100w Lump Sum + 1w/m DCA (239w invested)...")
    cfs_lump = build_cashflow_schedule(dates, initial_lump=1000000.0, dca_amount=10000.0, dca_freq="monthly")
    
    # 9-asset
    _, df_res_9_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, weights_9, sub_fee=sub_fee)
    m_9_lump = evaluate_portfolio(df_res_9_lump["total_asset"], df_res_9_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # 7-asset
    _, df_res_7_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, weights_7, sub_fee=sub_fee)
    m_7_lump = evaluate_portfolio(df_res_7_lump["total_asset"], df_res_7_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # Benchmark: SSE Composite (theoretical index)
    _, df_res_sh_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, {"sh_index_000001": 1.0}, sub_fee=sub_fee)
    m_sh_lump = evaluate_portfolio(df_res_sh_lump["total_asset"], df_res_sh_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # Benchmark: CSI 300 Investable Fund (050002)
    _, df_res_300_lump = run_chronological_simulation(dates, df_proxy, cfs_lump, {"csi300_price_index": 1.0}, sub_fee=sub_fee)
    m_300_lump = evaluate_portfolio(df_res_300_lump["total_asset"], df_res_300_lump["cumulative_invested"], cfs_lump, rf_annual)
    
    # -------------------------------------------------------------
    # Track 2: Scenario B - Pure Monthly DCA 1w/month (140w invested)
    # -------------------------------------------------------------
    print("--> Running Scenario B: Pure Monthly DCA (140w invested)...")
    cfs_dca = build_cashflow_schedule(dates, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")
    
    _, df_res_9_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, weights_9, sub_fee=sub_fee)
    m_9_dca = evaluate_portfolio(df_res_9_dca["total_asset"], df_res_9_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    _, df_res_7_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, weights_7, sub_fee=sub_fee)
    m_7_dca = evaluate_portfolio(df_res_7_dca["total_asset"], df_res_7_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    _, df_res_sh_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, {"sh_index_000001": 1.0}, sub_fee=sub_fee)
    m_sh_dca = evaluate_portfolio(df_res_sh_dca["total_asset"], df_res_sh_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    _, df_res_300_dca = run_chronological_simulation(dates, df_proxy, cfs_dca, {"csi300_price_index": 1.0}, sub_fee=sub_fee)
    m_300_dca = evaluate_portfolio(df_res_300_dca["total_asset"], df_res_300_dca["cumulative_invested"], cfs_dca, rf_annual)
    
    # -------------------------------------------------------------
    # Track 3: Scenario C - Weekly 3,150 RMB DCA Sensitivity Track
    # -------------------------------------------------------------
    print("--> Running Scenario C: Weekly 3,150 RMB DCA Sensitivity Track...")
    cfs_weekly = build_cashflow_schedule(dates, initial_lump=0.0, dca_amount=3150.0, dca_freq="weekly")
    _, df_res_7_weekly = run_chronological_simulation(dates, df_proxy, cfs_weekly, weights_7, sub_fee=sub_fee)
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
    _, df_res_common_9 = run_chronological_simulation(dates_common, df_true, cfs_common, true_weights_9, sub_fee=sub_fee)
    m_common_9 = evaluate_portfolio(df_res_common_9["total_asset"], df_res_common_9["cumulative_invested"], cfs_common, rf_annual)

    # -------------------------------------------------------------
    # Robustness: Leave-One-Out Asset Attribution (Scenario B Pure DCA)
    # -------------------------------------------------------------
    print("--> Running Leave-One-Out Asset Sensitivity Attribution...")
    loo_results = {}
    for dropped_asset in weights_9.keys():
        sub_weights = {k: v for k, v in weights_9.items() if k != dropped_asset}
        tot_w = sum(sub_weights.values())
        norm_weights = {k: v / tot_w for k, v in sub_weights.items()}
        _, df_loo = run_chronological_simulation(dates, df_proxy, cfs_dca, norm_weights, sub_fee=sub_fee)
        m_loo = evaluate_portfolio(df_loo["total_asset"], df_loo["cumulative_invested"], cfs_dca, rf_annual)
        loo_results[dropped_asset] = {
            "ending_value": round(m_loo["ending_value"], 2),
            "xirr": round(m_loo["xirr"], 4),
            "twr_max_drawdown": round(m_loo["twr_max_drawdown"], 4)
        }

    # Format JSON payload
    clean_metrics = {
        "version": "2.0.0",
        "generated_at": pd.Timestamp.now().isoformat(),
        "notes": "Machine-readable verified baseline metrics generated by run_all.py",
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
                    "sharpe_ratio": round(m_7_lump["sharpe_ratio"], 4)
                },
                "shanghai_index": {
                    "ending_value": round(m_sh_lump["ending_value"], 2),
                    "net_profit": round(m_sh_lump["net_profit"], 2),
                    "roi": round(m_sh_lump["roi"], 4),
                    "xirr": round(m_sh_lump["xirr"], 4),
                    "twr_max_drawdown": round(m_sh_lump["twr_max_drawdown"], 4)
                },
                "csi300_fund": {
                    "ending_value": round(m_300_lump["ending_value"], 2),
                    "net_profit": round(m_300_lump["net_profit"], 2),
                    "roi": round(m_300_lump["roi"], 4),
                    "xirr": round(m_300_lump["xirr"], 4),
                    "twr_max_drawdown": round(m_300_lump["twr_max_drawdown"], 4)
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
                    "sharpe_ratio": round(m_7_dca["sharpe_ratio"], 4)
                },
                "shanghai_index": {
                    "ending_value": round(m_sh_dca["ending_value"], 2),
                    "roi": round(m_sh_dca["roi"], 4),
                    "xirr": round(m_sh_dca["xirr"], 4),
                    "twr_max_drawdown": round(m_sh_dca["twr_max_drawdown"], 4)
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
            "leave_one_out_sensitivity": loo_results
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
    print("KEY REVENUE & RISK AUDIT RESULTS SUMMARY")
    print("=" * 70)
    print(f"1. Scenario A (100w + 1w/m DCA, Total 239w invested):")
    print(f"   - Canonical 9-Asset: Ending {m_9_lump['ending_value']/10000:.2f}w, XIRR {m_9_lump['xirr']*100:.2f}%, TWR MaxDD {m_9_lump['twr_max_drawdown']*100:.2f}%, Sharpe {m_9_lump['sharpe_ratio']:.2f}")
    print(f"   - Modified 7-Asset : Ending {m_7_lump['ending_value']/10000:.2f}w, XIRR {m_7_lump['xirr']*100:.2f}%, TWR MaxDD {m_7_lump['twr_max_drawdown']*100:.2f}%, Sharpe {m_7_lump['sharpe_ratio']:.2f}")
    print(f"   - SSE Composite    : Ending {m_sh_lump['ending_value']/10000:.2f}w, XIRR {m_sh_lump['xirr']*100:.2f}%, TWR MaxDD {m_sh_lump['twr_max_drawdown']*100:.2f}%")
    print(f"2. Scenario B (Pure Monthly 1w DCA, Total 140w invested):")
    print(f"   - Canonical 9-Asset: Ending {m_9_dca['ending_value']/10000:.2f}w, XIRR {m_9_dca['xirr']*100:.2f}%, Custom Profit DD {m_9_dca['custom_capital_ratio_drawdown']*100:.2f}%")
    print(f"   - Modified 7-Asset : Ending {m_7_dca['ending_value']/10000:.2f}w, XIRR {m_7_dca['xirr']*100:.2f}%, Custom Profit DD {m_7_dca['custom_capital_ratio_drawdown']*100:.2f}%")
    print(f"   - SSE Composite    : Ending {m_sh_dca['ending_value']/10000:.2f}w, XIRR {m_sh_dca['xirr']*100:.2f}%, Custom Profit DD {m_sh_dca['custom_capital_ratio_drawdown']*100:.2f}%")
    print(f"3. Real Fund Common Window (2023-2026, all 9 funds exist in reality):")
    print(f"   - True 9-Asset     : Ending {m_common_9['ending_value']/10000:.2f}w, XIRR {m_common_9['xirr']*100:.2f}%, Sharpe {m_common_9['sharpe_ratio']:.2f}")
    print("=" * 70)

if __name__ == "__main__":
    run_pipeline()
