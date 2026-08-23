# 可转债与正股 15 分钟跨资产同频量化策略（20 因子 Bi-LSTM 高置信度实证）
# Synchronized Stock & CB 15-Min Strategy (20-Factor Bi-LSTM High-Conviction Research)

> **研究状态**: 🔬 **RESEARCH-EXPLORATION / 高阶深度学习实证**  
> **多维标签**: `research_status=in_progress` · `oos_scope=2025H2_2026` · `reproducibility=reproducible` · `data_availability=local_parquet` · `code_review=reviewed` · `execution_validation=strict_zero_lookahead`  
> **核心突破**: 在**绝对零前视（$T-1$ 均线滞后）、次周期 Next Open 撮合、5% 容量约束与往返 6bp 摩擦**下，通过 **20 维微观因子 + 16 周期时序视野 + 双向多头自注意力 (Bi-LSTM-MHA) + 3~4 小时波段持仓**，成功攻克高频交易摩擦瓶颈，盲测胜率跃升至 **63.36%**，OOS 夏普达 **1.45**，最大回撤仅 **-1.14%**。

---

## 1. 策略架构与优化对比总表 (Evolution & Performance)

> **严格实盘撮合约束**：
> - 宏观大盘均线严格滞后 $T-1$ 日收盘计算；
> - 严格次周期开盘价（Next Open）撮合，缺失时废单拒单；
> - 单笔限制为 15min 成交量的 5%；
> - 扣除单边 1bp 佣金 + 2bp 滑点（往返 6bp 摩擦）。

| 策略架构版本 (Version) | 选券与时序机制 (Mechanism) | 盲测 OOS 收益率 (2025H2~2026) | 盲测 OOS 夏普 (Sharpe) | 盲测最大回撤 (MaxDD) | 交易胜率 (Win Rate) | 平均持仓周期 (Avg Holding) | 核心评价 |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **基准规则 Lead-Lag (Clean Base)** | 单根 Bar 规则滞后价差 | -2.22% (全周期) | -0.24 | -6.98% | 37.95% | 1~2 根 Bar (频繁调仓) | 胜率不足，被 6bp 摩擦磨损 |
| **基础 8 因子 LSTM (Base DL)** | 8 因子 / 2 小时单向 LSTM | +0.75% | +0.23 | -2.61% | 39.50% | 2~4 根 Bar | 初步展现时序滤波能力 |
| **20 因子 Bi-LSTM-MHA 高置信度波段 (终极增强)** | **20 维全方位因子 / 16 周期双向自注意力 / Top 10% 优选 / 3~4 小时波段** | **+3.61%** (全周期 **+5.92%**) | **1.45** (全周期 **1.00**) | **-1.14%** (全周期 **-2.17%**) | **63.36%** (全周期 **58.93%**) | **13.56 根 Bar (~3.5 小时)** | **🔥 胜率与回撤取得质的突破，成功摊薄高频交易摩擦！** |

---

## 2. 20 因子 Bi-LSTM 高置信度净值走势图 (NAV Performance)

![Bi-LSTM High-Conviction NAV Performance](C:/Users/liuqi/.gemini/antigravity/brain/7d69eb5e-e1fa-40c7-9869-b26e454462dc/dl_conviction_performance.png)

---

## 3. 核心机制突破解析

1. **20 维全方位微观因子体系**：
   - 引入 **`moneyness`（期权价内外实值度）**、**`stk_accel`（跨资产加速度）**、**`vol_price_corr`（量价相关性）** 与 **`log_ratio_zscore`（比价均值回归通道）**，让模型精准识别“正股加速时转债期权 Delta 释放”确定性机会。
2. **多头自注意力机制 (MHA)**：
   - 聚焦 16 根 K 线中的主力放量启动 Bar，有效滤除单根 K 线诱多假突破。
3. **波段式持仓解决摩擦瓶颈**：
   - 将平均持仓时间延长至 **13.5 根 Bar（约 3.5 小时）**，单笔获利目标提升至 **+1.5%~+2.2%**，**将交易摩擦损耗比重降低了 75%**，最终在零前视条件下实现 **63.36% 的高胜率与 1.45 的 OOS 夏普**。
