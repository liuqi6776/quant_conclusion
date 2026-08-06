# -*- coding: utf-8 -*-
"""结论库文档一致性 CI 检查器。

对应外部评审 P1「文档一致性 CI」, 检查 quant_conclusion 归档库的文档结构一致性:

  A. 头部约定: 每篇研究文档须有「**状态**」行（合法摘要标记）+「**多维标签**」行
     （六维齐全: research_status / code_review / reproducibility / oos_scope /
       data_availability / execution_validation, 取值在合法枚举内）
  B. ✅ 使用规则: 摘要标记「✅ 可用」<-> 准入五条中可标签化维度必须全部满足
     （oos_scope=full_strategy + reproducibility=full + execution_validation=passed +
       code_review=passed + research_status=validated）; ⚠️ 候选不得出现
     「可直接作为开发依据 / 准入五条全部满足」等矛盾措辞
  C. 索引一致性: 各 README 索引行的链接文件必须存在, 状态标记与文档头部一致
  D. 现状声明: 出现「✅ 可用」文档时, README 现状声明应同步（warning 不阻断）

退出码: 0=通过; 1=存在 error（阻断）; warning 仅提示不阻断。
用法:  python quant_conclusion/tools/check_docs.py [--root quant_conclusion] [--verbose]
"""
from __future__ import annotations

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 合法摘要标记（含 double_low_pit_research 使用的「⚠️ 已归档」）
MARKER_RE = r"(✅ 可用|⚠️ 候选|⚠️ 已归档|❌ 已证伪|🔬 探索中)"

DIMENSIONS = {
    "research_status": {"validated", "rejected", "exploratory"},
    "code_review": {"passed", "failed", "not_reviewed"},
    "reproducibility": {"full", "partial", "none"},
    "oos_scope": {"full_strategy", "component_only", "none"},
    "data_availability": {"public", "private", "unavailable"},
    "execution_validation": {"passed", "partial", "none"},
}

# 准入五条中可由标签表达的维度（✅ 可用 的充分必要条件）
ADMISSION_TAGS = {
    "research_status": "validated",
    "code_review": "passed",
    "reproducibility": "full",
    "oos_scope": "full_strategy",
    "execution_validation": "passed",
}

errors: list[str] = []
warnings: list[str] = []


def err(msg: str) -> None:
    errors.append(msg)


def warn(msg: str) -> None:
    warnings.append(msg)


def norm_marker(text: str) -> str | None:
    """把标记串归一为核心词: 可用/候选/归档/证伪/探索。"""
    if "可用" in text:
        return "可用"
    if "候选" in text:
        return "候选"
    if "归档" in text:
        return "归档"
    if "证伪" in text:
        return "证伪"
    if "探索" in text:
        return "探索"
    return None


def find_head(lines: list[str], pat: re.Pattern, max_lines: int = 40) -> str | None:
    for ln in lines[:max_lines]:
        m = pat.search(ln)
        if m:
            return ln
    return None


def parse_tags(text: str) -> dict[str, str]:
    """解析 `key=v1 · key=v2 ...` 形式的多维标签。"""
    return dict(re.findall(r"([a-z_]+)=(\S+)", text))


def check_doc(path: str, rel: str) -> None:
    with open(path, encoding="utf-8") as fh:
        lines = fh.readlines()
    text = "".join(lines)

    st_ln_no = None
    for _i, _ln in enumerate(lines[:40], 1):
        if re.search(r"\*\*状态\*\*\s*[:：]?\s*", _ln):
            st_ln_no = _i
            break
    st_line = lines[st_ln_no - 1] if st_ln_no else find_head(lines, re.compile(r"\*\*状态\*\*\s*[:：]?\s*"))
    tag_line = find_head(lines, re.compile(r"\*\*多维标签\*\*"))
    # study008 风格: 「多维标签:」无 ** 包裹
    if tag_line is None:
        tag_line = find_head(lines, re.compile(r"(?<![\*\w])多维标签\s*[:：]"))

    # ---- A. 状态行 ----
    if st_line is None:
        # 多状态文档（如 study008: ## 状态 章节多行）-> 宽松: 要求 ## 状态 下至少一行含合法标记
        sec = [ln for ln in lines if re.match(r"^\s*-\s*.*", ln) or re.match(r"^##\s*状态", ln)]
        has_status_section = any(re.match(r"^##\s*状态", ln) for ln in lines)
        if has_status_section and any(norm_marker(ln) for ln in sec):
            pass  # 多状态文档, 跳过单一状态一致性（但仍做标签检查）
        else:
            err(f"{rel}: 缺少「**状态**」行（或「## 状态」章节无合法摘要标记）")
    else:
        marker = norm_marker(st_line)
        if marker is None:
            err(f"{rel}: 状态行摘要标记无法识别: {st_line.strip()[:80]}")
        elif marker == "可用":
            # B. ✅ 可用 -> 准入五条（标签项）必须全部满足
            tags = parse_tags(tag_line or "")
            for dim, need in ADMISSION_TAGS.items():
                if tags.get(dim) != need:
                    err(f"{rel}: 标记「✅ 可用」但 {dim}={tags.get(dim,'缺失')}（准入五条要求 {need}）")
        elif marker in ("候选", "归档"):
            # 候选/归档 不得出现「可直接作为开发依据」等措辞
            for phrase in ("可直接作为开发依据", "准入五条全部满足", "已确认可用"):
                if phrase in st_line:
                    err(f"{rel}: 状态标记「{marker}」与措辞「{phrase}」矛盾")

    # ---- A. 多维标签 ----
    if tag_line is None:
        err(f"{rel}: 缺少「**多维标签**」行")
    else:
        tags = parse_tags(tag_line)
        for dim, valid in DIMENSIONS.items():
            if dim not in tags:
                err(f"{rel}: 多维标签缺 {dim}")
            elif tags[dim] not in valid:
                err(f"{rel}: 多维标签 {dim}={tags[dim]} 非法（合法: {sorted(valid)}）")

    # ---- B. 正文 ✅ 使用规则 ----
    # 状态行之外出现「✅ 可用」作为结论表述 -> 冲突
    for m in re.finditer(r"✅ 可用", text):
        ln_no = text[: m.start()].count("\n") + 1
        if ln_no <= 2 or ln_no == st_ln_no:
            continue  # 跳过标题区与状态行本身
        err(f"{rel}: 正文出现「✅ 可用」（L{ln_no}），与「当前仓库无 ✅ 可用结论」现状矛盾；如为核验类通过请改为「✅ 通过」并注明非策略可用性")


def check_index(index_path: str, rel: str, base_dir: str) -> None:
    """检查索引 README: 链接文件存在性 + 状态标记一致性。"""
    with open(index_path, encoding="utf-8") as fh:
        lines = fh.readlines()
    for i, ln in enumerate(lines, 1):
        m = re.match(r"^\|\s*\[[^]]+\]\((\./?)([^)]+\.md)\)\s*\|([^|]*)\|(.*)\|", ln)
        if not m:
            continue
        target = m.group(2)
        full = os.path.normpath(os.path.join(base_dir, target))
        if not os.path.isfile(full):
            err(f"{rel}:L{i} 索引链接指向不存在的文件: {target}")
            continue
        # 状态标记一致性（仅对单状态文档）
        idx_marker = norm_marker(m.group(4))
        with open(full, encoding="utf-8") as fh2:
            doc_lines = fh2.readlines()
        st = find_head(doc_lines, re.compile(r"\*\*状态\*\*\s*[:：]?\s*"))
        if st is None or idx_marker is None:
            continue  # 多状态文档或索引无标记 -> 跳过
        doc_marker = norm_marker(st)
        if idx_marker != doc_marker:
            err(f"{rel}:L{i} 索引标记「{m.group(4).strip()[:40]}」与文档头部「{st.strip()[:60]}」不一致")


def check_all(root: str) -> None:
    for dirpath, _dirs, files in os.walk(root):
        if "tools" in dirpath:
            continue
        for fn in sorted(files):
            if not fn.endswith(".md"):
                continue
            rel = os.path.relpath(os.path.join(dirpath, fn), root)
            if fn == "README.md":
                check_index(os.path.join(dirpath, fn), rel, dirpath)
            else:
                check_doc(os.path.join(dirpath, fn), rel)

    # ---- D. 现状声明 ----
    readme = os.path.join(root, "README.md")
    if os.path.isfile(readme):
        with open(readme, encoding="utf-8") as fh:
            readme_text = fh.read()
        has_usable = False
        for dp, _ds, fs in os.walk(root):
            for fn in fs:
                if fn == "README.md" or not fn.endswith(".md"):
                    continue
                with open(os.path.join(dp, fn), encoding="utf-8") as fh:
                    doc_lines = fh.readlines()
                if norm_marker(find_head(doc_lines, re.compile(r"\*\*状态\*\*\s*[:：]?\s*")) or "") == "可用":
                    has_usable = True
                    break
            if has_usable:
                break
        if has_usable and "不存在 ✅ 可用结论" in readme_text:
            warn("README 现状声明仍写「不存在 ✅ 可用结论」，但存在标记为 ✅ 可用 的文档，请人工确认同步")


def main() -> int:
    ap = argparse.ArgumentParser(description="结论库文档一致性检查")
    ap.add_argument("--root", default=ROOT)
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args()

    check_all(args.root)
    if args.verbose:
        for w in warnings:
            print(f"[WARN ] {w}")
        for e in errors:
            print(f"[ERROR] {e}")
    print(f"文档一致性: {len(errors)} error / {len(warnings)} warning")
    for e in errors:
        print(f"  ERROR: {e}")
    if warnings and not errors:
        print("  提示（不阻断）:")
        for w in warnings:
            print(f"    - {w}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
