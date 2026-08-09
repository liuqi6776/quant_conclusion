# quant_conclusion

量化交易研究结论归档库。将各研究仓库中**经过验证/审计的结论**按资产品类归档，避免结论散落在各个仓库中难以检索。

## 状态标记约定

### 摘要标记（一档制，快速浏览）

| 标记 | 含义 |
|------|------|
| ✅ 可用 | 满足下方"可用准入五条"**全部**条件，可独立验证、可直接作为策略/因子开发依据 |
| ⚠️ 候选 | 有正向证据但**未满足全部准入标准**（当前绝大多数正向结论落在此档），仅可参考，不可直接作为开发依据 |
| ❌ 已证伪 | 经过验证后确认无效的假设（负结果同样重要，避免重复踩坑） |
| 🔬 探索中 | 尚未完成验证，仅记录方向 |

> ⚠️ 现状（2026-08 审查后）：**当前仓库不存在 ✅ 可用结论**。原因：无自动回归测试、数据/代码不可独立复现、**仅 21 因子 IC 层做了多重检验（BH-FDR/Bonferroni/DSR），完整研究选择过程未控制**。所有正向结论均为 ⚠️ 候选，按多维标签判断证据强度。

### 可用准入五条（全部满足才可标 ✅）

1. 完整策略有严格 OOS（`oos_scope=full_strategy`）；
2. 数据和代码可独立复现（`reproducibility=full`）；
3. 执行模型覆盖真实约束（`execution_validation=passed`：按实际换手计费、涨跌停/停牌/容量/延迟）；
4. 结果由自动测试锁定（实验 → `expected_metrics.json` 对比 → 无 diff）；
5. 研究选择过程经过多重检验控制（FDR / Deflated Sharpe / 冻结验证集）。

### 多维状态标签（每篇研究文件头部标注）

摘要标记只回答"能不能直接用"；**多维标签**正交描述证据强度，避免用一个 ✅ 表达所有含义：

| 维度 | 取值 | 含义 |
|------|------|------|
| `research_status` | validated / rejected / exploratory | 研究结论状态（统计/回测层面） |
| `code_review` | passed / failed / not_reviewed | 代码审查状态 |
| `reproducibility` | full / partial / none | 独立复现程度（数据+代码） |
| `oos_scope` | full_strategy / component_only / none | 样本外验证范围 |
| `data_availability` | public / private / unavailable | 数据可得性 |
| `execution_validation` | passed / partial / none | 执行层验证（成本/涨跌停/容量/延迟） |

## 品类索引

- [股票 STOCK](./STOCK/README.md)
  - [风格中性化指数增强（final_quant）](./STOCK/style_neutralized_index_enhancement.md) — ⚠️ 候选（因子 NW 显著；无 OOS、无法回源复现、MaxDD 待回源复核）
  - [回撤控制：MA20 三档（risk_control）](./STOCK/risk_control.md) — ⚠️ 候选（风控层有 2018-2019 跨期支持；完整策略 OOS 未验证、私有数据不可独立复现）
  - [多资产避险配置：RS12 弱段资产替换（quant-system）](./STOCK/defensive_asset_allocation.md) — ⚠️ 候选（单周期 2020~2026 风险预算方案，未证明跨宏观周期稳健）
  - [期权增强型全局策略 Study 005（quant-system）](./STOCK/option_enhanced_study005.md) — ❌ 已证伪（Sharpe 3.08 无法复现）
  - [新闻情感与股价预测（news_stock_research）](./STOCK/news_sentiment_prediction.md) — ❌ 已证伪（显著性检验未通过）
  - [筹码边际因子与主力资金流互补（iFinD 实测）](./STOCK/chip_moneyflow_complement.md) — ⚠️ 候选（因子 IC 显著，独立 alpha 温和，建议作过滤因子）
  - [新闻情绪温度计辅助择时（设计）](./STOCK/news_sentiment_timing.md) — 🔬 探索中
  - [因子字典 21 因子验证（factor_dic）](./STOCK/factor_dic_validation.md) — ⚠️ 候选（统计检验 + 21 因子 IC 层多重检验完成；候选因子待冻结后独立 OOS）
  - [特质换手波动率 turnover_vol_20](./STOCK/turnover_vol_20.md) — ⚠️ 候选（ICIR 0.750；21 因子 IC 层已做多重检验；无独立 OOS，完整选择过程未控制，主组合全期跑输基准）
  - [市场状态研究（regime_study）](./STOCK/regime_study.md) — ⚠️ 候选（描述性研究，供因子理解与择时参考）
  - [风格因子增量（style_factors）](./STOCK/style_factors.md) — ⚠️ 候选（样本内价值系显著增量；无独立 OOS）
  - [WorldQuant Alpha101 因子验证](./STOCK/alpha101_factors.md) — ❌ 已证伪（月频下无增量）
  - [study_008 增量增强路径验证（quant_system_v2）](./STOCK/study008_incremental_enhancements.md) — ⚠️ 基线候选（样本内强局部最优）/ ❌ 六条增量路径全部证伪 / ✅ PIT 数据端核验通过（工程核验，非策略可用性）
- [ETF](./ETF/README.md)
  - [A股ETF期权 Max Pain 研究（quant-research）](./ETF/max_pain_etf_options.md) — ⚠️ 候选（少量结论已回测，大部分未验证）
- [可转债 CB](./CB/README.md)
  - [可转债双低 PIT 策略研究（CB_research）](./CB/double_low_pit_research.md) — ⚠️ 已归档（工程框架 5 轮审计 PASS；策略决议 Halt & Archive）
  - [双低池跨资产轮动框架（设计）](./CB/double_low_rotation.md) — 🔬 探索中
- [场外基金 FUND](./FUND/README.md)
  - [场外基金稳健组合：低相关分散 + 量化/AI 增强（quant_system_v2）](./FUND/otc_fund_stable_portfolio.md) — ⚠️ 候选（完整回测含费用模型；权重迭代选择、无独立 OOS、数据本地私有）
  - [基金研究教训汇总：4433/择时/凯利/低相关分散/再平衡](./FUND/otc_fund_lessons.md) — ⚠️ 候选（多结论文档，含 ❌ 证伪子项与 🔬 探索方向）

## 使用规则

1. 只有 **✅ 可用** 的结论可作为策略/因子开发的直接依据；⚠️ 候选仅用于继续研究，❌ 和 🔬 仅用于避坑/方向记录。
2. 每个结论文件必须标注：来源仓库、验证方式、验证区间、数据/结论有效期、**六维状态标签**。
3. 新增已确认结论时，先判断品类归属，再在对应目录追加文件，并更新本索引。
4. 摘要状态升级（候选 → 可用）必须补齐准入五条证据；任何"已确认/可用"表述必须与多维标签一致，不得混用。
5. 结论标注"结论有效期"（信号类通常 6-12 个月），到期后自动降级为 ⚠️ 候选并安排复检。
