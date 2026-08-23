# 可转债与正股 15 分钟跨资产同频量化策略（审计作废与整改记录）
# Synchronized Stock & CB 15-Min Strategy (Audit Invalidation & Remediation Record)

> **审查结论**: ❌ **FAIL / 回测作废（存在明确日内前视未来函数与选样偏差，严禁用于实盘）**  
> **多维标签**: `research_status=invalidated_due_to_lookahead` · `oos_scope=none` · `reproducibility=non_reproducible` · `data_availability=private` · `code_review=failed` · `execution_validation=lookahead_detected`  
> **审查对象**: `Convertible_Bond_research` (main@809c7994) 与 `quant_conclusion` (main@0077e13d)  
> **核心决议**: **停止引用 44.70% 累计收益与 Sharpe 1.63 指标，全系统状态降级，策略严禁实盘部署。**

---

## 1. 审查发现的致命缺陷清单 (Critical Flaws Identified)

### 缺陷 1：日内大盘前视未来函数（Lookahead Bias）
代码在计算当日大盘中位数均线状态时，使用了当天全天 15 分钟的收盘价计算当日中位数：
```python
daily_mkt = full_df.groupby("trade_date_str").agg({"close": "median"})
daily_mkt["mkt_bull_ma"] = daily_mkt["mkt_median_price"] >= daily_mkt["mkt_ma20"]
# 合并回同一天的全部 15 分钟记录
```
- **影响**: 早盘 09:45、10:00 的开仓信号间接使用了当天 15:00 收盘价，属于**严重前视偏差**，使原有所有收益率与夏普比率完全失真作废。
- **整改标准**: 大盘择时指标必须严格滞后至 $T-1$ 交易日，日内仅可使用该时点前可见的历史数据。

### 缺陷 2：样本选择偏差与幸存者偏差（Sample Selection Bias）
代码在加载转债时，按文件大小降序截取前 100 个文件：
```python
valid_cb_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
target_cb_files = valid_cb_files[:max_cb_files]
```
- **影响**: 文件最大代表存续时间最长、交易最活跃、极少早退市或暴雷的标的，引入了强烈的**流动性偏差与幸存者偏差**，不代表 1030 只全市场真实回测。

### 缺陷 3：撮合与执行模型不够真实（Execution Flaws）
- `next_open` 缺失时回退到当前 `close` 成交（违反严格次周期开盘原则）；
- 14:45 退出使用当前 bar 价格（同 bar 信号同 bar 成交）；
- 未对 15 分钟成交量设置严谨参与率限制（单笔 20 万元占 150 万成交额的 13%，固定 2bps 滑点严重失真）。

### 缺陷 4：转股价与强赎生命周期非 PIT（Point-in-Time Gaps）
- 转股价使用静态 `cb_basic_info.csv`，未追踪历史分红、送配股及下修公告生效日；
- 强赎过滤仅按单一日期精确匹配 `(cb_code, trade_date) in call_set`，未处理公告后至退市前的完整风险窗口。

---

## 2. 状态调整与当前可转债配置结论

1. **15 分钟同频高频策略**: **当前回测彻底作废，评级 FAIL，严禁实盘**。
2. **月频双低 Top10 策略**: **维持 Halt & Archive 归档状态**。Sharpe 0.91 低于被动 ETF 511380 (0.95)，且容量公式存在 10 倍错误（`0.5` 误写为 50%）。
3. **双低跨资产轮动**: **属于纯概念设计（Exploratory），无回测支持，不能实盘**。

> **当前最可信的量化配置结论**：  
> **现有主动可转债策略尚未证明风险调整后优于 511380 ETF，也没有通过实盘准入要求。被动持有 511380 是当前证据支持的最优可转债敞口基准。**
