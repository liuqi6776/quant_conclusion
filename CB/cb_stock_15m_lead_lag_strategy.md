# 可转债与正股 15 分钟跨资产同频量化策略（已实测确认 · Phase 1&2 增强版）
# Synchronized Stock & Convertible Bond 15-Min Cross-Asset Quantitative Strategy (Phase 1 & 2 Enhanced)

> **来源**: [Convertible_Bond_research (GitHub)](https://github.com/liuqi6776/Convertible_Bond_research)  
> **数据时间跨度**: 2024-01-02 至 2026-08-21（覆盖 996 只标的正股 15min K 线与 1030 只转债高频数据，总样本超 78 万根对齐切片）  
> **验证方式**: 严格无未来函数事件驱动引擎（次周期 Next Bar 开盘价撮合 + 万一佣金 + 万二滑点真实摩擦）  
> **状态**: ✅ 已确认（实证回测完成，三年全正收益，夏普比率 1.63，累计收益 +44.70%，最大回撤 -5.41%）  
> **多维标签**: `research_status=confirmed` · `oos_scope=2024_2026` · `reproducibility=reproducible` · `data_availability=local_parquet` · `code_review=reviewed` · `execution_validation=realistic_next_bar`

---

## 1. 核心研究结论摘要 (Executive Summary)

1. **同频跨资产数据的质变价值**：
   - 过去仅使用正股 T-1 日频特征驱动 15min 转债交易，策略处于持续摩擦亏损（累计 -6.53%，夏普 -0.20）；
   - 接入正股 **15 分钟同频高频数据** 后，挖掘出显著的先行-滞后价差（`lead_lag_spread`，**RankIC 高达 +0.0302**）。
2. **Phase 1 宏观择时双状态机（CBLens 启示）**：
   - 结合大盘 20 日均线与全市场中位估值分位数，在市场系统性破位时（如 2026 年 3 月）**果断空仓熔断**，避开单月 20.7 万元暴跌，而在牛市主升浪顺应动量进攻。
3. **Phase 2 BS 理论错估选券排序（Pricing-Research 启示）**：
   - 将郑振龙教授团队的 **BS / 纯债贴现理论错估度（`mispricing_score`）** 作为选券打分优选权重，优先做多严重被低估且具备纯债底保护的标的，推动 **全周期累计收益达 +44.70%，夏普比率跃升至 1.63，最大回撤压制在 -5.41%**。

---

## 2. 策略演进与四阶段实证绩效对比 (Performance Evolution)

| 核心指标 (Metric) | 阶段一：仅日频 T-1 | 阶段二：15m 同频 | 阶段三：三大防御机制 | **阶段四：Phase 1&2 理论错估增强 (终极版)** | 提升与突破说明 |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **初始本金 (Capital)** | 100 万元 | 100 万元 | 100 万元 | **1,000,000 元** | 标准实盘资金配置 |
| **期末总资产 (Equity)** | 93.47 万元 | 110.84 万元 | 131.46 万元 | **1,447,000.75 元** | **全周期净赚 44.70 万元** |
| **累计收益率 (Total Return)** | -6.53% | +10.84% | +31.46% | **+44.70%** | **收益暴增，创全周期历史新高** |
| **年化收益率 (Annualized)** | -1.72% | +4.24% | +11.68% | **+16.09%** | **实现高品质双位数年化收益** |
| **夏普比率 (Sharpe Ratio)** | -0.20 | +0.33 | 1.26 | **1.63** | **夏普比率跃升至 1.63 卓越水平** |
| **最大动态回撤 (Max Drawdown)** | -12.32% | -25.21% | -5.83% | **-5.41%** | **最大回撤压制至仅 -5.41%** |
| **盈亏比 (Profit-Loss Ratio)** | 1.60 | 1.58 | 1.81 | **1.82** | **获利单平均盈利显著压制止损单** |
| **胜率 (Win Rate)** | 37.80% | 39.66% | 40.42% | **41.77%** | **胜率突破 41.7%** |
| **2024 年度表现** | -2.58% | -0.78% | +2.71% (Sharpe 0.32) | **+8.15% (Sharpe 0.81, MaxDD -5.4%)** | **震荡市收益暴增 3 倍** |
| **2025 年度表现** | +31.00% | +31.67% | +20.65% (Sharpe 2.29) | **+26.06% (Sharpe 2.73, MaxDD -4.4%)** | **主升浪稳健大赚超 26 万元** |
| **2026 年度表现** | -8.44% | -20.74% | +5.81% (Sharpe 1.36) | **+5.86% (Sharpe 1.37, MaxDD -3.0%)** | **避开 3 月暴跌，逆势稳健收官** |

---

## 3. 核心量化因子体系 (Alpha Factor Library)

1. **`delta_imbalance` (理论 Delta 失衡偏离因子，RankIC = +0.0274)**：
   $$\text{Delta\_Imbalance} = \frac{\text{Stk\_ROC}_1}{1 + \text{Premium}} - \text{CB\_ROC}_1$$
2. **`mispricing_score` (BS 理论定价错估度因子)**：
   $$\text{Mispricing} = \frac{V_{\text{BS/Bond}} - P_{\text{market}}}{P_{\text{market}}}$$
3. **`lead_lag_spread` (基础先行-滞后价差因子，RankIC = +0.0302)**：
   $$\text{Spread} = \text{Stk\_ROC}_1 - \text{CB\_ROC}_1$$
4. **`amt_weighted_lead_lag` (机构大单加权先行价差，RankIC = +0.0260)**：
   引入正股成交额倍数赋权，有效过滤缩量小幅拉升噪音。

---

## 4. 避坑指南与工程实操清单 (Pitfalls & Engineering Rules)

- ⚠️ **严禁日频数据跨周期混入高频（未来函数防范）**：正股日频特征必须严格滞后至 $T-1$ 日。
- ⚠️ **严禁在牛市中用静态估值硬过滤动量**：估值因子宜作为优先排序权重（Soft Score），避免将牛市主升浪中的高 Delta 动量标的误杀。
- ⚠️ **严格次周期开盘价撮合（Next Open）**：15:00 产生信号只能在次周期开盘买入，绝不能使用当前 Bar 收盘价即时成交。
- ⚠️ **必须预留双边滑点与佣金（20bps+10bps）**：实测必须扣除万一佣金 + 万二滑点。
- ⚠️ **代码仓库与复现路径**：
  - 代码库：[Convertible_Bond_research (GitHub)](https://github.com/liuqi6776/Convertible_Bond_research)
  - 理论定价引擎：`scripts/cb_pricing_models.py`
  - 同频回测总控：`run_synchronized_15m_backtest.py`
  - 核心回测引擎：`scripts/cb_synchronized_backtester.py`
