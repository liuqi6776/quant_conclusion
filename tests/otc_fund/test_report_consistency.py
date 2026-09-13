# -*- coding: utf-8 -*-
"""
Automated Document vs. Expected Metrics Consistency Test
========================================================
Ensures that all key performance metrics, capital valuations, XIRRs, and
drawdowns reported across FUND/*.md documents exactly match the canonical
values locked in configs/otc_fund/expected_metrics.json.
Prevents silent documentation drift upon future re-runs or refactoring.
"""
import os
import json
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(REPO_ROOT, "configs", "otc_fund", "expected_metrics.json")
STABLE_DOC = os.path.join(REPO_ROOT, "FUND", "otc_fund_stable_portfolio.md")
DCA_DOC = os.path.join(REPO_ROOT, "FUND", "otc_fund_dca_2015_2026.md")


@pytest.fixture(scope="module")
def expected_metrics():
    assert os.path.exists(CONFIG_PATH), f"Missing {CONFIG_PATH}"
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def stable_doc_content():
    assert os.path.exists(STABLE_DOC), f"Missing {STABLE_DOC}"
    with open(STABLE_DOC, "r", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(scope="module")
def dca_doc_content():
    assert os.path.exists(DCA_DOC), f"Missing {DCA_DOC}"
    with open(DCA_DOC, "r", encoding="utf-8") as f:
        return f.read()


def test_expected_metrics_json_structure(expected_metrics):
    """Verify expected_metrics.json exists and conforms to standard institutional schema."""
    assert "version" in expected_metrics
    assert "scenarios" in expected_metrics
    assert "metrics_tolerances" in expected_metrics


def test_scenario_b_consistency(expected_metrics, stable_doc_content, dca_doc_content):
    """Verify Scenario B (Pure Monthly 1w DCA) numbers match across docs and JSON."""
    sc_b = expected_metrics["scenarios"]["pure_monthly_1w_dca"]["modified_7_asset"]
    exp_val_w = f"{sc_b['ending_value'] / 10000.0:.2f} 万元"
    exp_val_w_short = f"{sc_b['ending_value'] / 10000.0:.2f}w"
    exp_xirr = f"{sc_b['xirr'] * 100:.2f}%"
    exp_dd = f"{sc_b['twr_max_drawdown'] * 100:.2f}%"

    assert exp_val_w in stable_doc_content or exp_val_w_short in stable_doc_content
    assert exp_xirr in stable_doc_content
    assert exp_dd in stable_doc_content
    assert exp_val_w_short in dca_doc_content or exp_val_w in dca_doc_content
    assert exp_xirr in dca_doc_content
    assert exp_dd in dca_doc_content


def test_scenario_a_consistency(expected_metrics, stable_doc_content):
    """Verify Scenario A (100w Lump + 1w/m DCA) numbers match in stable portfolio doc."""
    sc_a = expected_metrics["scenarios"]["lump_100w_plus_monthly_1w"]["modified_7_asset"]
    exp_val_w = f"{sc_a['ending_value'] / 10000.0:.2f} 万元"
    exp_xirr = f"{sc_a['xirr'] * 100:.2f}%"
    exp_dd = f"{sc_a['twr_max_drawdown'] * 100:.2f}%"

    assert exp_val_w in stable_doc_content
    assert exp_xirr in stable_doc_content
    assert exp_dd in stable_doc_content


def test_counterfactual_consistency(expected_metrics, stable_doc_content):
    """Verify Counterfactual (No-Active) numbers match in stable portfolio doc."""
    cf_b = expected_metrics["scenarios"]["pure_monthly_1w_dca"]["counterfactual_no_active"]
    exp_val_b = f"{cf_b['ending_value'] / 10000.0:.2f} 万元"
    exp_xirr_b = f"{cf_b['xirr'] * 100:.2f}%"
    exp_dd_b = f"{cf_b['twr_max_drawdown'] * 100:.2f}%"

    assert exp_val_b in stable_doc_content
    assert exp_xirr_b in stable_doc_content
    assert exp_dd_b in stable_doc_content

    cf_a = expected_metrics["scenarios"]["lump_100w_plus_monthly_1w"]["counterfactual_no_active"]
    exp_val_a = f"{cf_a['ending_value'] / 10000.0:.2f} 万元"
    exp_xirr_a = f"{cf_a['xirr'] * 100:.2f}%"
    exp_dd_a = f"{cf_a['twr_max_drawdown'] * 100:.2f}%"

    assert exp_val_a in stable_doc_content
    assert exp_xirr_a in stable_doc_content
    assert exp_dd_a in stable_doc_content


def test_leave_one_out_consistency(expected_metrics, stable_doc_content):
    """Verify Leave-One-Out sensitivity table numbers match expected_metrics."""
    loo = expected_metrics["scenarios"]["leave_one_out_sensitivity"]
    for asset_key, metrics in loo.items():
        val_w = f"{metrics['ending_value'] / 10000.0:.2f} 万元"
        xirr_pct = f"{metrics['xirr'] * 100:.2f}%"
        dd_pct = f"{metrics['twr_max_drawdown'] * 100:.2f}%"

        assert val_w in stable_doc_content, f"LOO asset {asset_key} value {val_w} missing in doc"
        assert xirr_pct in stable_doc_content, f"LOO asset {asset_key} XIRR {xirr_pct} missing in doc"
        assert dd_pct in stable_doc_content, f"LOO asset {asset_key} MaxDD {dd_pct} missing in doc"


def test_rolling_horizon_matrix_consistency(expected_metrics, stable_doc_content, dca_doc_content):
    """Verify Rolling Horizon Matrix statistical disclosures match across docs."""
    matrix = expected_metrics["scenarios"]["rolling_horizon_matrix"]

    for horizon_key, h_data in matrix.items():
        n_windows = str(h_data["num_rolling_windows"])
        n_eff = f"{h_data['effective_independent_windows']:.1f}"
        median_xirr = f"{h_data['median_xirr'] * 100:.2f}%"
        ci = h_data["bootstrap_ci_95_median_xirr"]
        ci_str = f"[{ci[0] * 100:.2f}%, {ci[1] * 100:.2f}%]"

        assert n_windows in stable_doc_content, f"Rolling {horizon_key} windows {n_windows} missing"
        assert n_eff in stable_doc_content, f"Rolling {horizon_key} Neff {n_eff} missing"
        assert median_xirr in stable_doc_content, f"Rolling {horizon_key} median {median_xirr} missing"
        assert ci_str in stable_doc_content, f"Rolling {horizon_key} CI {ci_str} missing in stable doc"

        assert n_windows in dca_doc_content, f"Rolling {horizon_key} windows {n_windows} missing in dca doc"
        assert n_eff in dca_doc_content, f"Rolling {horizon_key} Neff {n_eff} missing in dca doc"
        assert median_xirr in dca_doc_content, f"Rolling {horizon_key} median {median_xirr} missing in dca doc"
        assert ci_str in dca_doc_content, f"Rolling {horizon_key} CI {ci_str} missing in dca doc"


def test_scenario_c_weekly_consistency(expected_metrics, dca_doc_content):
    """Verify Weekly 3,150 DCA figures match exact calculation."""
    weekly = expected_metrics["scenarios"]["weekly_3150_dca"]
    exp_val = f"{weekly['ending_value'] / 10000.0:.2f} 万元"
    exp_xirr = f"{weekly['xirr'] * 100:.2f}%"
    exp_dd = f"{weekly['twr_max_drawdown'] * 100:.2f}%"
    exp_periods = f"{int(weekly['invested_total'] / 3150.0)} 期"

    assert exp_val in dca_doc_content, f"Weekly DCA ending value {exp_val} missing"
    assert exp_xirr in dca_doc_content, f"Weekly DCA XIRR {exp_xirr} missing"
    assert exp_dd in dca_doc_content, f"Weekly DCA MaxDD {exp_dd} missing"
    assert exp_periods in dca_doc_content, f"Weekly DCA periods {exp_periods} missing"


def test_start_date_sensitivity_2016(expected_metrics, dca_doc_content):
    """Verify 2016 circuit breaker start date sensitivity rounding."""
    start_2016 = expected_metrics["scenarios"]["start_date_sensitivity"]["2016_circuit_breaker_bottom"]["modified_7_asset"]
    exp_val = f"{start_2016['ending_value'] / 10000.0:.2f}w"
    exp_xirr = f"{start_2016['xirr'] * 100:.2f}%"
    exp_dd = f"{start_2016['twr_max_drawdown'] * 100:.2f}%"

    expected_pattern = f"{exp_val} ({exp_xirr} / {exp_dd})"
    assert expected_pattern in dca_doc_content, f"Expected '{expected_pattern}' in DCA doc"


def test_benchmarks_consistency(expected_metrics, stable_doc_content):
    """Verify passive broad index and shanghai index match across docs."""
    p_b = expected_metrics["scenarios"]["pure_monthly_1w_dca"]["passive_broad_index"]
    sh_b = expected_metrics["scenarios"]["pure_monthly_1w_dca"]["shanghai_index"]
    
    val_pb = f"{p_b['ending_value'] / 10000.0:.2f} 万元"
    xirr_pb = f"{p_b['xirr'] * 100:.2f}%"
    dd_pb = f"{p_b['twr_max_drawdown'] * 100:.2f}%"
    assert val_pb in stable_doc_content
    assert xirr_pb in stable_doc_content
    assert dd_pb in stable_doc_content
    
    val_sh = f"{sh_b['ending_value'] / 10000.0:.2f} 万元"
    xirr_sh = f"{sh_b['xirr'] * 100:.2f}%"
    dd_sh = f"{sh_b['twr_max_drawdown'] * 100:.2f}%"
    assert val_sh in stable_doc_content
    assert xirr_sh in stable_doc_content
    assert dd_sh in stable_doc_content


def test_vol_target_table_consistency(expected_metrics, stable_doc_content):
    """Verify all figures in the VolTarget comparison table match expected_metrics."""
    vt = expected_metrics["scenarios"]["vol_target_proportional_control_experiment"]
    ol = vt["open_loop"]
    pc = vt["proportional_control_kp_025"]
    
    assert f"{ol['ending_value'] / 10000.0:.2f} 万元" in stable_doc_content
    assert f"{ol['xirr'] * 100:.2f}%" in stable_doc_content
    assert f"{ol['realized_vol'] * 100:.2f}%" in stable_doc_content
    assert f"{ol['vol_tracking_error'] * 100:.2f}%" in stable_doc_content
    assert f"{ol['multiplier_churn']:.2f}" in stable_doc_content
    assert f"{ol['sharpe_ratio']:.4f}" in stable_doc_content
    
    assert f"{pc['ending_value'] / 10000.0:.2f} 万元" in stable_doc_content
    assert f"{pc['xirr'] * 100:.2f}%" in stable_doc_content
    assert f"{pc['realized_vol'] * 100:.2f}%" in stable_doc_content
    assert f"{pc['vol_tracking_error'] * 100:.2f}%" in stable_doc_content
    assert f"{pc['multiplier_churn']:.2f}" in stable_doc_content
    assert f"{pc['sharpe_ratio']:.4f}" in stable_doc_content


def test_correlation_matrix_consistency(stable_doc_content):
    """Verify that the 7-asset correlation table printed in stable_portfolio.md matches panel data."""
    import pandas as pd
    panel_p = os.path.join(REPO_ROOT, "data", "otc_fund", "fund_dca_daily_panel_2015_2026.csv")
    df = pd.read_csv(panel_p, index_col=0, parse_dates=True)
    cols = ['bond_pure_000015', 'dividend_100032', 'money_market_000198', 'proxy_quant_a', 'gold_000216', 'nasdaq_000834', 'proxy_global_tech']
    corr = df[cols].pct_change().dropna().corr()
    
    # Assert printed mean
    assert "0.1192" in stable_doc_content
    assert "0.0996" in stable_doc_content
    
    # Check key printed pairs exist in markdown
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            v = corr.iloc[i, j]
            v_str = f"{v:.3f}"
            assert v_str in stable_doc_content, f"Correlation pair {cols[i]}-{cols[j]} ({v_str}) missing in doc"


