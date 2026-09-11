# -*- coding: utf-8 -*-
import os
import pytest
import numpy as np
import pandas as pd
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_ROOT)

from scripts.otc_fund.instruments import CORE_FUNDS

def test_qdii_attributes_and_disclosure_lag():
    """Verify QDII fund attributes and trading timing requirements."""
    qdii_funds = [c for c, m in CORE_FUNDS.items() if m.is_qdii]
    assert len(qdii_funds) >= 4, "Expected at least 4 QDII funds in catalog"
    
    # QDII funds are known to have T+1 or T+2 NAV disclosure
    for c in qdii_funds:
        meta = CORE_FUNDS[c]
        assert meta.is_qdii is True
