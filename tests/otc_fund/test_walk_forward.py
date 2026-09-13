# -*- coding: utf-8 -*-
"""
Walk-Forward Optimization & Risk Parity Engine Tests
====================================================
Verifies:
1. Strict zero-lookahead temporal isolation: max(train_dates) < rebalance_date.
2. Constrained risk parity bounds: 0.05 <= w_i <= 0.35 and sum(w_i) == 1.0.
3. Ledoit-Wolf shrinkage covariance validity (symmetric, positive definite, 0 <= lambda <= 1).
4. Dynamic chronological ledger execution with time-varying walk-forward schedules.
5. Deterministic reproducibility across independent runs.
"""
import os
import sys
import pytest
import numpy as np
import pandas as pd

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.walk_forward import (
    estimate_shrinkage_covariance,
    solve_constrained_risk_parity,
    generate_walk_forward_schedule,
    compute_walk_forward_weights,
)
from scripts.otc_fund.ledger import run_chronological_simulation
from scripts.otc_fund.cashflows import build_cashflow_schedule
from scripts.otc_fund.metrics import evaluate_portfolio


PROXY_CSV = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", "asset_class_proxy_panel_2015_2026.csv")


@pytest.fixture(scope="module")
def panel_data():
    assert os.path.exists(PROXY_CSV), f"Proxy panel missing: {PROXY_CSV}"
    df = pd.read_csv(PROXY_CSV, index_col=0, parse_dates=True)
    return df


def test_walk_forward_strict_lookahead_isolation(panel_data):
    """Assert that for every walk-forward step, max(train_dates) < rebalance_date."""
    dates = panel_data.index
    schedule = generate_walk_forward_schedule(dates, train_months=36, step_months=12)
    assert len(schedule) >= 8, f"Expected at least 8 yearly walk-forward periods, got {len(schedule)}"

    for step in schedule:
        rebal_dt = step["rebalance_date"]
        train_end = step["train_end_date"]
        train_start = step["train_start_date"]

        # Strict temporal inequality
        assert train_end < rebal_dt, f"Temporal leakage: train_end {train_end} >= rebal_dt {rebal_dt}"
        assert train_start < train_end, f"Inverted training dates: {train_start} >= {train_end}"


def test_constrained_risk_parity_bounds_and_sum():
    """Verify that solved weights strictly satisfy box constraints [0.05, 0.35] and sum to 1.0."""
    np.random.seed(42)
    asset_names = [f"asset_{i}" for i in range(6)]
    # Random positive definite covariance
    A = np.random.randn(6, 6)
    cov = A @ A.T + np.eye(6) * 0.1

    weights = solve_constrained_risk_parity(
        cov_matrix=cov,
        asset_names=asset_names,
        box_constraints=(0.05, 0.35),
        target_sum=1.0,
    )

    total_w = sum(weights.values())
    assert abs(total_w - 1.0) < 1e-6, f"Weights do not sum to 1.0: {total_w}"

    for a, w in weights.items():
        assert 0.05 - 1e-6 <= w <= 0.35 + 1e-6, f"Weight out of bounds for {a}: {w}"


def test_shrinkage_covariance_properties(panel_data):
    """Verify Ledoit-Wolf shrinkage produces a valid, symmetric positive-definite covariance matrix."""
    risk_assets = ["bond_pure_000015", "dividend_100032", "proxy_quant_a", "gold_000216", "nasdaq_000834", "proxy_global_tech"]
    returns_df = panel_data[risk_assets].pct_change().dropna()
    train_rets = returns_df.iloc[:750]

    cov, shrinkage = estimate_shrinkage_covariance(train_rets)

    assert 0.0 <= shrinkage <= 1.0, f"Shrinkage parameter out of bounds: {shrinkage}"
    assert np.allclose(cov, cov.T), "Covariance matrix is not symmetric"

    eigenvalues = np.linalg.eigvalsh(cov)
    assert np.all(eigenvalues > 0), f"Covariance matrix is not positive-definite: min eig = {eigenvalues.min()}"


def test_walk_forward_simulation_execution(panel_data):
    """Verify end-to-end chronological ledger simulation with dynamic walk-forward weights."""
    risk_assets = ["bond_pure_000015", "dividend_100032", "proxy_quant_a", "gold_000216", "nasdaq_000834", "proxy_global_tech"]
    weights_df, weights_by_date = compute_walk_forward_weights(
        nav_df=panel_data,
        risk_assets=risk_assets,
        cash_asset="money_market_000198",
        cash_weight=0.10,
        train_months=36,
        step_months=12,
        box_constraints=(0.05, 0.35),
    )

    assert not weights_df.empty
    assert len(weights_by_date) >= 9

    dates = panel_data.index
    cfs = build_cashflow_schedule(dates, initial_lump=0.0, dca_amount=10000.0, dca_freq="monthly")

    ledger, df_res = run_chronological_simulation(
        trading_dates=dates,
        nav_df=panel_data,
        cashflow_schedule=cfs,
        target_weights=weights_by_date,
    )

    metrics = evaluate_portfolio(df_res["total_asset"], df_res["cumulative_invested"], cfs, 0.02)

    assert metrics["ending_value"] > 2500000.0, f"Ending value too low: {metrics['ending_value']}"
    assert 0.10 <= metrics["xirr"] <= 0.20, f"XIRR out of reasonable bounds: {metrics['xirr']}"
    assert -0.20 <= metrics["twr_max_drawdown"] <= 0.0, f"MaxDD out of bounds: {metrics['twr_max_drawdown']}"
    assert metrics["sharpe_ratio"] > 0.80, f"Sharpe too low: {metrics['sharpe_ratio']}"


def test_walk_forward_deterministic_reproducibility(panel_data):
    """Verify that independent runs of compute_walk_forward_weights yield identical weights."""
    risk_assets = ["bond_pure_000015", "dividend_100032", "proxy_quant_a", "gold_000216", "nasdaq_000834", "proxy_global_tech"]
    _, w1 = compute_walk_forward_weights(panel_data, risk_assets)
    _, w2 = compute_walk_forward_weights(panel_data, risk_assets)

    assert w1.keys() == w2.keys()
    for dt in w1:
        for a in w1[dt]:
            assert abs(w1[dt][a] - w2[dt][a]) < 1e-8, f"Non-deterministic weight for {a} on {dt}"
