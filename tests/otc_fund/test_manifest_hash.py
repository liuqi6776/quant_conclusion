# -*- coding: utf-8 -*-
import os
import json
import hashlib
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_file_hash(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
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
