# 可转债与正股 15 分钟跨资产同频量化策略（审计作废与标准零前视回测基准）
# Synchronized Stock & CB 15-Min Strategy (Audit Invalidation & Clean Baseline)

> **审查结论**: ❌ **FAIL / 回测作废（存在明确日内大盘前视未来函数与选样偏差，严禁用于实盘）**  
> **多维标签**: `research_status=invalidated_due_to_lookahead` · `oos_scope=none` · `reproducibility=reproducible` · `data_availability=private` · `code_review=reviewed` · `execution_validation=zero_lookahead_benchmarked`  
> **审查对象**: `Convertible_Bond_research` 与 `quant_conclusion`  
> **核心决议**: **全面作废 44.70% 累计收益与 Sharpe 1.63 虚高指标，公布标准零前视真实基准。**

---

## 1. 严格零前视标准回测基准 (Standard Zero-Lookahead Baseline)

在完成审计整改（大盘均线严格滞后 $T-1$ 日、消除按文件大小选券的幸存者偏差、强制次周期开盘价且缺失时废单拒单、施加 5% Bar 成交量上限并扣除单边 1bp 佣金 + 2bp 滑点）后，**标准真实的无前视回测表现** 如下：

| 核心指标 | 原虚高指标 (前视作废) | **标准零前视实测指标 (Clean Baseline)** | 说明 |
| :--- | :---: | :---: | :--- |
| **初始本金** | 100 万元 | **1,000,000 元** | 标准实盘资金 |
| **期末总资产** | 144.70 万元 (作废) | **977,847.61 元** | 真实净亏损 -2.22 万元 |
| **累计收益率** | +44.70% (作废) | **-2.22%** | **真实无前视收益（旧版指标彻底作废）** |
| **年化收益率** | +16.09% (作废) | **-0.96%** | 扣除真实摩擦后处于磨损状态 |
| **夏普比率 (Sharpe)** | 1.63 (作废) | **-0.24** | **真实夏普比率为负** |
| **最大动态回撤** | -5.41% | **-6.98%** | 真实全周期最大回撤 |
| **盈亏比 (Profit/Loss)** | 1.82 | **1.54** | 获利单平均盈利与止损单比值 |
| **交易胜率** | 41.77% | **37.95%** | 真实次周期开盘撮合胜率 |
| **有效交易总笔数** | 1,652 笔 | **614 笔** | 在真实流动性约束下的有效交易 |
| **2024 年表现** | +8.15% (作废) | **-1.86% (Sharpe -0.41, MaxDD -5.58%)** | 真实无前视表现 |
| **2025 年表现** | +26.06% (作废) | **-0.87% (Sharpe -0.33, MaxDD -4.08%)** | 真实无前视表现 |
| **2026 年表现** | +5.86% (作废) | **+0.51% (Sharpe 0.51, MaxDD -1.28%)** | 真实无前视表现 |

---

## 2. 真实净值走势图 (True Zero-Lookahead NAV Curve)

![Clean Zero Lookahead NAV Curve](C:/Users/liuqi/.gemini/antigravity/brain/7d69eb5e-e1fa-40c7-9869-b26e454462dc/cb_clean_performance.png)

---

## 3. 当前最终量化配置结论

> **现有主动可转债策略（15分钟策略 / 月频双低Top10）尚未证明风险调整后优于 511380 被动 ETF，均不满足实盘准入要求。被动持有 511380 是当前证据支持的最优基准。**
