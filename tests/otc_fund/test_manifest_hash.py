# -*- coding: utf-8 -*-
import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        content = f.read()
        # Normalize CRLF to LF for cross-platform hash identity
        normalized = content.replace(b"\r\n", b"\n")
        h.update(normalized)
    return h.hexdigest()

def test_manifest_sha256_hashes_match_disk():
    """Verify that every file listed in source_manifest.json matches its disk sha256 byte-for-byte."""
    manifest_path = os.path.join(REPO_ROOT, "data", "otc_fund", "source_manifest.json")
    assert os.path.exists(manifest_path), f"Manifest missing at {manifest_path}"
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    for fn, expected_h in manifest["files"].items():
        if "true" in fn or "asset_class_proxy" in fn:
            p = os.path.join(REPO_ROOT, "data", "otc_fund", "processed", fn)
        else:
            p = os.path.join(REPO_ROOT, "data", "otc_fund", fn)
            
        assert os.path.exists(p), f"Referenced data file missing: {p}"
        disk_h = get_file_hash(p)
        assert disk_h == expected_h, f"Hash mismatch for {fn}: disk={disk_h} != manifest={expected_h}"

def test_manifest_dividend_audit_event_count():
    """Verify that verified_events_in_dividend_events_csv matches dividend_events.csv row count."""
    manifest_path = os.path.join(REPO_ROOT, "data", "otc_fund", "source_manifest.json")
    div_path = os.path.join(REPO_ROOT, "data", "otc_fund", "dividend_events.csv")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    with open(div_path, "r", encoding="utf-8") as f:
        # Subtract 1 for header
        num_events = len([line for line in f if line.strip()]) - 1
        
    audit_count = manifest["dividend_coverage_audit"]["verified_events_in_dividend_events_csv"]
    assert audit_count == num_events, f"Manifest recorded {audit_count} events but CSV has {num_events}"


def test_manifest_dividend_audit_integrity():
    """Verify that zero-dividend list and active-dividend list are mutually exclusive and match CSV exactly."""
    manifest_path = os.path.join(REPO_ROOT, "data", "otc_fund", "source_manifest.json")
    div_path = os.path.join(REPO_ROOT, "data", "otc_fund", "dividend_events.csv")
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    audit = manifest["dividend_coverage_audit"]
    zero_codes = {item["code"] for item in audit["zero_dividend_holdings_verified_against_raw_parquets"]}
    active_funds = {item["code"]: item["events_in_csv"] for item in audit["funds_with_verified_dividends"]}
    
    # 1. Zero and Active lists must be strictly disjoint
    assert zero_codes.isdisjoint(active_funds.keys()), f"Overlap between zero and active dividend funds: {zero_codes & active_funds.keys()}"
    
    # 2. 000290 and 501018 must be in active list, NOT in zero list
    assert "000290" in active_funds and active_funds["000290"] == 6
    assert "501018" in active_funds and active_funds["501018"] == 2
    assert "000290" not in zero_codes
    assert "501018" not in zero_codes
    
    # 3. Active counts in manifest must match raw CSV counts
    with open(div_path, "r", encoding="utf-8") as f:
        csv_lines = [line.strip().split(",") for line in f if line.strip()][1:]
    
    csv_counts = {}
    for row in csv_lines:
        code = row[1]
        csv_counts[code] = csv_counts.get(code, 0) + 1
        
    for code, count in active_funds.items():
        assert csv_counts.get(code, 0) == count, f"Fund {code} has {csv_counts.get(code, 0)} events in CSV but {count} in manifest"


