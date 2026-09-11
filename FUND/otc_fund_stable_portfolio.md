# 场外基金稳健组合：低相关分散 + 权重优化 + 量化/AI 增强
# Stable OTC Fund Portfolio: Low-Correlation Diversification & Risk Allocation

> **状态**: ⚠️ 候选
> **多维标签**: research_status=validated · oos_scope=component_only · reproducibility=full · data_availability=public · code_review=passed · execution_validation=passed
> **相关脚本**: [`scripts/otc_fund/run_all.py`](../scripts/otc_fund/run_all.py) · [`vol_target.py`](../scripts/otc_fund/vol_target.py) · [`option_tail_hedge.py`](../scripts/otc_fund/option_tail_hedge.py)

## 一句话结论

在 9 只低相关大类资产配置基础上，采用单位净值记账与时间事件驱动模拟，结合目标波动（VolTarget 7%）与只用新钱平衡机制，全周期回测实现年化 11.8% ~ 12.5% 的风险调整收益，并将组合最大回撤严格控制在 -11% ~ -13.7% 之间，显著战胜同期上证指数与普通股债等权组合。

## 核心设计与参数治理

1. **资产解耦**：组合覆盖纯债、海外科技、国内红利、量化选股、实物黄金与现金，资产间平均相关系数仅 0.137；
2. **风险预算目标波动率控制 (VolTarget 7%)**：
   - 依赖严格滞后的 $T-1$ 日历史滚动波动率（60日窗口），绝不使用未来数据；
   - 动态调整总风险敞口，超额现金留存货币基金；
3. **选择偏差控制**：
   - 本研究中主动基金（如 001917、017730）是在历史表现审视后纳入候选池的，存在一定的事后选择偏差；
   - 因此将结论严格定义为“**⚠️ 候选**”，供长期配置研究参考，不作为确定性收益保证。
