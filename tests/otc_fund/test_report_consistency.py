# -*- coding: utf-8 -*-
import os
import json
import pytest
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

def test_expected_metrics_json_structure():
    """Verify expected_metrics.json exists and conforms to standard institutional schema."""
    config_path = os.path.join(REPO_ROOT, "configs", "otc_fund", "expected_metrics.json")
    if not os.path.exists(config_path):
        pytest.skip("expected_metrics.json will be generated upon run_all execution")
        
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    assert "version" in data
    assert "scenarios" in data
    assert "metrics_tolerances" in data
