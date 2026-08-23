# 可转债 CB

可转债品类已确认研究成果索引。

| 文件 | 主题 | 状态 | 实盘建议 |
|------|------|------|----------|
| [cb_stock_15m_lead_lag_strategy.md](./cb_stock_15m_lead_lag_strategy.md) | 可转债与正股 15 分钟跨资产同频量化策略 | ❌ **FAIL / 回测作废**（审查发现存在日内大盘前视未来函数与选样偏差，44.70%/Sharpe 1.63 停止引用） | 🚫 严禁实盘部署 |
| [double_low_pit_research.md](./double_low_pit_research.md) | 双低 PIT 策略 + 零前视回测框架 | ⚠️ **已归档**（框架 5 轮审计 PASS / 策略决议 Halt & Archive，Sharpe 0.91 < 511380 的 0.95） | 🚫 不建议主动实盘 |
| [double_low_rotation.md](./double_low_rotation.md) | 双低池跨资产轮动框架（股票池↔转债池↔511380） | 🔬 **探索中**（纯框架设计，无回测数据） | 🚫 概念设计不能实盘 |

> **核心结论**: 现有主动可转债策略尚未证明风险调整后优于 511380 ETF，也没有通过实盘准入要求。
