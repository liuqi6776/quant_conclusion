# -*- coding: utf-8 -*-
"""
Unit Tests for Circular Block Bootstrap (Politis & Romano 1992)
==============================================================
Validates:
1. Deterministic reproducibility under fixed seed.
2. Fast DCA XIRR solver numerical convergence and accuracy.
3. Proper handling of edge cases (short series, zero variance).
4. Statistical conservatism: CBB confidence interval on overlapping windows
   is strictly wider than naive iid bootstrap.
"""
import pytest
import numpy as np
from scripts.otc_fund.metrics import fast_dca_xirr, circular_block_bootstrap_median_xirr

def test_fast_dca_xirr_accuracy():
    """Verify fast_dca_xirr converges accurately to constant growth rate."""
    # 1% per month = (1.01)^12 - 1 = 12.6825%
    rets = np.full(36, 0.01)
    xirr = fast_dca_xirr(rets)
    expected = (1.01 ** 12.0) - 1.0
    assert xirr == pytest.approx(expected, rel=1e-3)

def test_fast_dca_xirr_short_or_invalid():
    """Verify edge cases return NaN."""
    assert np.isnan(fast_dca_xirr(np.array([])))
    assert np.isnan(fast_dca_xirr(np.array([0.05])))

def test_circular_block_bootstrap_reproducibility():
    """Verify exact reproducibility under fixed random seed."""
    np.random.seed(123)
    rets = np.random.normal(0.008, 0.03, 120)
    
    ci1 = circular_block_bootstrap_median_xirr(rets, h_months=36, block_length=12, n_resamples=200, seed=42)
    ci2 = circular_block_bootstrap_median_xirr(rets, h_months=36, block_length=12, n_resamples=200, seed=42)
    
    assert ci1 == ci2
    assert ci1[0] < ci1[1]

def test_cbb_is_wider_than_naive_iid_on_autocorrelated_data():
    """Verify that Circular Block Bootstrap produces a wider, more honest CI than naive iid on autocorrelated returns."""
    # Generate autocorrelated monthly returns: r_t = 0.6 * r_{t-1} + eps
    np.random.seed(99)
    T = 140
    eps = np.random.normal(0.005, 0.02, T)
    rets = np.zeros(T)
    for t in range(1, T):
        rets[t] = 0.6 * rets[t-1] + eps[t]
        
    H = 36
    # 1. CBB CI
    ci_low_cbb, ci_high_cbb = circular_block_bootstrap_median_xirr(rets, h_months=H, block_length=12, n_resamples=500, seed=42)
    cbb_width = ci_high_cbb - ci_low_cbb
    
    # 2. Naive iid bootstrap on rolling window XIRRs
    rolling_xirrs = [fast_dca_xirr(rets[i:i+H]) for i in range(T - H + 1)]
    np.random.seed(42)
    naive_meds = [float(np.median(np.random.choice(rolling_xirrs, size=len(rolling_xirrs), replace=True))) for _ in range(500)]
    naive_width = np.percentile(naive_meds, 97.5) - np.percentile(naive_meds, 2.5)
    
    # CBB must be strictly wider than naive iid on autocorrelated data
    assert cbb_width > naive_width, f"CBB width ({cbb_width:.4f}) should be wider than naive iid ({naive_width:.4f})"
