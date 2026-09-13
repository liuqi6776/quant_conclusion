# -*- coding: utf-8 -*-
"""
Rolling Walk-Forward Optimization Engine
========================================
Implements institutional-grade out-of-sample parameter generation:
1. Analytical Ledoit-Wolf covariance matrix shrinkage (reduces estimation noise for collinear assets).
2. Constrained Equal Risk Contribution (ERC / Risk Parity) solver with box bounds [0.05, 0.35].
3. Strict zero-lookahead date isolation asserting max(train_dates) < rebalance_date.
4. Generates dynamic out-of-sample target weights time series without hindsight selection.
"""

import os
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from sklearn.covariance import ledoit_wolf


def estimate_shrinkage_covariance(returns_df: pd.DataFrame) -> Tuple[np.ndarray, float]:
    """
    Estimate regularized covariance matrix using Ledoit-Wolf shrinkage.
    Returns:
        (shrunk_cov_matrix, shrinkage_intensity)
    """
    X = returns_df.dropna().values
    if len(X) < 10:
        raise ValueError(f"Insufficient return samples for covariance estimation: {len(X)}")
    shrunk_cov, shrinkage = ledoit_wolf(X)
    return shrunk_cov, float(shrinkage)


def solve_constrained_risk_parity(cov_matrix: np.ndarray,
                                  asset_names: List[str],
                                  box_constraints: Tuple[float, float] = (0.05, 0.35),
                                  target_sum: float = 1.0,
                                  l2_penalty: float = 0.0,
                                  target_weights_ref: Optional[Dict[str, float]] = None) -> Dict[str, float]:
    """
    Solve Constrained Equal Risk Contribution (ERC) portfolio weights:
        min_w sum_i ( (w_i * (Sigma w)_i / (w^T Sigma w)) - 1/N )^2 + lambda * ||w - w_ref||^2
        s.t.  l_i <= w_i <= u_i,  sum_i w_i = target_sum
    """
    N = len(asset_names)
    if cov_matrix.shape != (N, N):
        raise ValueError(f"Covariance shape {cov_matrix.shape} does not match asset count {N}")

    bounds = [box_constraints for _ in range(N)]
    constraints = {'type': 'eq', 'fun': lambda w: np.sum(w) - target_sum}

    w_ref = None
    if l2_penalty > 0 and target_weights_ref:
        w_ref = np.array([target_weights_ref.get(a, target_sum / N) for a in asset_names])

    def objective(w: np.ndarray) -> float:
        var_p = float(w.T @ cov_matrix @ w)
        if var_p <= 1e-12:
            return 1e6
        # Marginal risk contribution
        rc = w * (cov_matrix @ w) / var_p
        target_rc = 1.0 / N
        loss = float(np.sum((rc - target_rc) ** 2))
        if l2_penalty > 0 and w_ref is not None:
            loss += float(l2_penalty * np.sum((w - w_ref) ** 2))
        return loss

    w0 = np.ones(N) * target_sum / N
    result = minimize(objective, w0, method='SLSQP', bounds=bounds, constraints=constraints, tol=1e-8)

    if not result.success:
        # Fallback to equal weights under bounds
        w_res = np.clip(w0, box_constraints[0], box_constraints[1])
        w_res = w_res / np.sum(w_res) * target_sum
    else:
        w_res = np.clip(result.x, box_constraints[0], box_constraints[1])
        w_res = w_res / np.sum(w_res) * target_sum

    return {asset: float(w) for asset, w in zip(asset_names, w_res)}


def generate_walk_forward_schedule(trading_dates: pd.DatetimeIndex,
                                   train_months: int = 36,
                                   step_months: int = 12) -> List[Dict[str, Any]]:
    """
    Generate non-overlapping or rolling walk-forward calibration timeline.
    Enforces strict temporal order: train_end < rebalance_date.
    """
    start_dt = trading_dates[0]
    end_dt = trading_dates[-1]

    schedule = []
    first_rebal_target = start_dt + pd.DateOffset(months=train_months)
    avail_dates = trading_dates[trading_dates >= first_rebal_target]
    if len(avail_dates) == 0:
        return []

    cur_year = avail_dates[0].year
    end_year = end_dt.year

    for yr in range(cur_year, end_year + 1):
        year_dates = trading_dates[trading_dates.year == yr]
        if len(year_dates) == 0:
            continue
        rebal_dt = year_dates[0]
        train_end = trading_dates[trading_dates < rebal_dt][-1]
        train_start = trading_dates[trading_dates <= (train_end - pd.DateOffset(months=train_months))]
        train_start_dt = train_start[-1] if len(train_start) > 0 else start_dt

        assert train_end < rebal_dt, f"Temporal leakage: train_end {train_end} >= rebal_dt {rebal_dt}"

        schedule.append({
            'rebalance_year': yr,
            'rebalance_date': rebal_dt,
            'train_start_date': train_start_dt,
            'train_end_date': train_end
        })

    return schedule


def compute_walk_forward_weights(nav_df: pd.DataFrame,
                                 risk_assets: List[str],
                                 cash_asset: Optional[str] = 'money_market_000198',
                                 cash_weight: float = 0.10,
                                 initial_weights: Optional[Dict[str, float]] = None,
                                 train_months: int = 36,
                                 step_months: int = 12,
                                 box_constraints: Tuple[float, float] = (0.05, 0.35)) -> Tuple[pd.DataFrame, Dict[pd.Timestamp, Dict[str, float]]]:
    """
    Compute full rolling walk-forward dynamic weight trajectory.
    Returns:
        (weights_table_df, schedule_weights_dict)
    """
    trading_dates = nav_df.index
    returns_df = nav_df[risk_assets].pct_change().dropna()
    schedule = generate_walk_forward_schedule(trading_dates, train_months=train_months, step_months=step_months)

    risk_target_sum = 1.0 - (cash_weight if cash_asset else 0.0)

    weights_by_date = {}
    history_records = []

    # Initial period prior to first walk-forward rebalance
    if initial_weights is None:
        init_risk_w = {a: risk_target_sum / len(risk_assets) for a in risk_assets}
        if cash_asset:
            init_risk_w[cash_asset] = cash_weight
        initial_weights = init_risk_w

    weights_by_date[trading_dates[0]] = initial_weights

    for item in schedule:
        rebal_dt = item['rebalance_date']
        t_start = item['train_start_date']
        t_end = item['train_end_date']

        train_rets = returns_df.loc[t_start:t_end]
        assert train_rets.index[-1] < rebal_dt, f"Lookahead detected: {train_rets.index[-1]} >= {rebal_dt}"

        cov, shrinkage = estimate_shrinkage_covariance(train_rets)
        solved_risk_w = solve_constrained_risk_parity(
            cov_matrix=cov,
            asset_names=risk_assets,
            box_constraints=box_constraints,
            target_sum=risk_target_sum
        )

        full_w = {a: solved_risk_w[a] for a in risk_assets}
        if cash_asset:
            full_w[cash_asset] = cash_weight

        tot_w = sum(full_w.values())
        full_w = {k: v / tot_w for k, v in full_w.items()}

        weights_by_date[rebal_dt] = full_w

        rec = {
            'rebalance_date': rebal_dt.strftime('%Y-%m-%d'),
            'rebalance_year': item['rebalance_year'],
            'train_start': t_start.strftime('%Y-%m-%d'),
            'train_end': t_end.strftime('%Y-%m-%d'),
            'train_days': len(train_rets),
            'shrinkage': round(shrinkage, 4)
        }
        for a in risk_assets:
            rec[a] = round(full_w[a] * 100.0, 2)
        if cash_asset:
            rec[cash_asset] = round(full_w[cash_asset] * 100.0, 2)
        history_records.append(rec)

    weights_df = pd.DataFrame(history_records)
    return weights_df, weights_by_date
