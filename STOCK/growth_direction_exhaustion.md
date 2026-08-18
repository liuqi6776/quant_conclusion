# 股票 GBDT/ENS 选股增长方向穷举总结（quant_system_v2）

> - **来源仓库**：`quant_system_v2`（research/sector_rotation + research/studies/study_008）
> - **验证方式**：滚动 walk-forward OOS（2023-2025 36 月，仅用 ≤m-1 数据训练 LGBM）+ 同窗 A/B 对比 + 单因子 IC 筛查 + 模型级滚动 WFO
> - **验证区间**：2020-01 ~ 2026-08（中证1000 成分股 PIT 月度快照，含退市股）
> - **数据**：tushare 量价/财务/涨停/龙虎榜 + 本地筹码（cyq）/主力资金流；万1 双边成本、申购 0.15%、赎回按持有期分级
> - **结论有效期**：月度调仓策略，量价信号半衰期约 6-12 个月，建议定期复检

## 状态

- **基线（GBDT C8 选股 + s123 择时 + V8 避险 + 目标波动率 7%）**: ⚠️ 候选 — 滚动 WFO OOS ICIR 2.44 为当前天花板，但无完整策略独立 OOS / 选择过程未多重检验控制
  - 多维标签: research_status=validated · oos_scope=component_only · reproducibility=partial · data_availability=private · code_review=not_reviewed · execution_validation=partial
- **收益层增量路线（扩标的池 / panel因子扩充 / Alpha101-191 / LSTM融合）**: ❌ 已证伪 — 全部无增量或过拟合
- **组合/风险层联动优化（DD-自适应波动率 / 滞回熔断 / 波动率状态×门槛）**: ❌ 已证伪 — 三条路线全部无增量
- **组合内加权（风险平价：逆波动率 / 逆方差）**: ❌ 已证伪 — 等权仍最优
- **情绪因子（涨停 / 龙虎榜）**: ❌ 已证伪 — 模型级滚动 WFO 全退化
- **数据端核验（幸存者偏差 / PIT）**: ✅ 通过 — 1986 只 PIT 月度成分快照，54 只退市股影响 <1%（工程核验，非策略可用性）

## 当前最优基线（天花板）

### 收益层：GBDT C8（个股 alpha 已封顶）

- **C8 特征（10 个）**：`ivol`、`ret_1m`、`momentum_20`、`volatility_20`、`alpha_006`、`alpha_012`、`enh4_score`（4 因子合成增强分）、`vwap_20_resid`、`float_pnl_20_resid`、`chip_shift_5_resid`（后三者为对 CHIP_BASE 正交化的筹码残差）
- **模型**：`LGBMRegressor(n_estimators=500, lr=0.05, num_leaves=7, max_depth=3, min_child_samples=80, reg_lambda=2.0, reg_alpha=0.1)`，早停验证用训练集末 3 月
- **滚动 WFO 口径**：OOS 自 20230101 起 36 月，仅用 ≤m-1 数据训练 → **OOS IC=0.084 / ICIR=2.44（年化）**，正率 81%

### 组合/风险层：UNDERVAL_T60_V8VT6_NL（等权基线）

| 指标 | 值 |
|---|---|
| 选股池 | 低估板块池（剔除价值陷阱）内 GBDT 打分 Top60 |
| 择时 | s123 信号（沪深300 PE-TTM 10年分位 <20% / ERP>均值+1σ / 沪深300回撤≤-25%），3进1出 |
| 避险 | V8 = 511990 短债 + 511260 信用债 + 518880 黄金 等权 |
| 波动率 | 目标波动率 7%（vol_tgt=0.06~0.07, floor=0.5） |
| 加权 | 等权（见"组合内加权"证伪结论） |
| 回测 | CAGR **9.71%** / MaxDD **-17.73%** / Sharpe **1.05** / Calmar **0.55** |

> 上述为"个股端"组合基线。另有一条**ETF 端 T7 基线**（等权 20 只传统行业 ETF + 同一 s123 信号），历史上跑赢个股端——核心原因是等权 20 ETF 天然分散 + 传统行业池本身是低估值策略 + s123 在 ETF 上更有效（流动性好/无个股暴雷/滑点低）。详见 [stock_gbdt_ens_s123_timing.md](./stock_gbdt_ens_s123_timing.md)。

## 增长方向穷举表（全部证伪 / 无增量）

### 收益层（个股 alpha 增量）

| 方向 | 核心实验 | 结果 | 判定 | 证据 |
|---|---|---|---|---|
| 资金利用率 | 满仓 vs 限投 | 满仓年化 16.8-21.6% vs 限投 7.8-8.0%；资金利用率是收益主导变量，满仓已是极限 | ✅ 满仓为既定设计（限投被否） | `backtest_undervalued_sector_stock.py` |
| 扩标的池 / 纳成长 | 板块之上统一 ML（universe_safe_hit30） | 无增量，已关闭 | ❌ 已证伪 | `train_universe_safe_hit30.py` / `backtest_universe_v2.py` |
| panel 内因子扩充 | 补量价因子 / 打分层 / 因子加权 / 财务因子（ROE/GM/LEV/GROW/SGROW） | 全部无增量或不占优；财务单因子 IC<0.02 | ❌ 已证伪 | [study008_incremental_enhancements.md](./study008_incremental_enhancements.md) |
| Alpha101 / Alpha191 | 79 因子 / 中证1000 / 78 月 | 最强单因子 alpha_040 ICIR 仅 0.68，全库无 ≥1.0；C8 加原始因子 IC 0.084→0.033、ICIR 2.44→0.93 | ❌ 已证伪 | [alpha101_factors.md](./alpha101_factors.md) |
| LSTM 时序融合 | GBDT+时序 LSTM（等权 / 滚动岭回归 meta-learner） | 纯 GBDT ICIR 2.68 最优，等权融合 1.49、岭回归 1.69 更差 | ❌ 已证伪 | `diag_gbdt_lstm_fusion_wfo.py` |

### 组合/风险层（杠杆与仓位）

| 方向 | 核心实验 | 结果 | 判定 |
|---|---|---|---|
| DD-自适应波动率目标 | 回撤越深，目标波动率与暴露下限同步下调 | Calmar 0.55→0.50，MaxDD -17.7%→**-19.4%**（trailing drawdown 是滞后指标，削减的是反弹暴露） | ❌ 已证伪 |
| 滞回熔断 | dd_scale 记忆最差回撤 + 3% 修复缓冲 | 与无滞回熔断结果完全一致（Calmar 0.50），月频再平衡下滞回跨不过月度 | ❌ 已证伪 |
| 波动率状态×进场门槛 | 高波动需 s123=3、低波动放宽至 s123=2 | Calmar 0.23、CAGR 5.0%，严重退化（放宽进场重复 entry_th=2 失败教训） | ❌ 已证伪 |

### 组合内加权（风险平价）

| 加权方式 | Calmar | 判定 |
|---|---|---|
| 等权（基线） | **0.55** | ✅ 最优 |
| 逆波动率 60 / 120 日 | 0.52 / 0.50 | ❌ 跑输 |
| 逆方差 60 / 120 日 | 0.53 / 0.51 | ❌ 跑输 |

> 逆波动率加权偏向低波动边缘股（低波动≠高预期收益），稀释 GBDT 已按打分选出的 TopN 暴露。

### 情绪层（涨停 / 龙虎榜）

| 因子 | 单因子 IC | 滚动 WFO 结果 | 判定 |
|---|---|---|---|
| 封单金额均值 zt_fd_amount_mean | -0.058（t=-5.55，与现有 7 因子相关性 max 0.144） | C8 ICIR 2.44→**1.63** | ❌ 退化 |
| 月涨停次数 zt_cnt_1m | -0.059（与 ivol 相关 0.567） | C8 ICIR 2.44→2.13 | ❌ 退化 |
| 龙虎榜净买额 net_amount | -0.005（不显著） | — | ❌ 排除 |

> 数据 PIT 可得、字段完整（封单/炸板/净买额 100% 非空，涨停覆盖 14.3% 股-月），但落到非线性 GBDT 滚动 WFO 后增量消失（特征增多→过拟合），且涨停/上榜次数被 ivol/momentum 覆盖。证据：`diag_sentiment_gbdt_wfo.py`。

## 方法论教训（反复出现的假阳性模式）

1. **单切分 / 线性正交 IC 会系统性高估任何新因子的增量**——Alpha101、LSTM 融合、情绪因子三次重演同一模式：线性正交 IC 显示"独立增量"，落到非线性 GBDT 滚动 WFO 后消失。**因子/模型有效性的最终判定必须以模型级滚动 WFO 为准。**
2. **等权跑赢优化权重**——个股层等权优于风险平价，ETF 层等权天然分散，与"低相关资产等权优于 min-variance/max-Sharpe"的既有经验一致。
3. **用 trailing drawdown 做自适应降风险是反生产**——回撤是滞后指标，检测到时下跌已发生，削减的是反弹暴露而非下跌暴露。
4. **A 股择时应在定投节奏上做，不在存量调仓上做**——存量调仓择时被静态持有完胜（期末 254 万 vs 237 万），卖 A 股腾现金反而踏空纳指+黄金+全球成长。
5. **验证集参与选参必过拟合**——仅训练期选参的纯 GBDT 在真 OOS（2025）年化 -2.9%/夏普 -0.11，坐实此前 V5-BEST 的"验证集过拟合"。

## 剩余可探索方向（供新增长方向接手）

> 以下方向基于既有结论的未竟线索，均未验证，属 🔬 探索中，非结论。

1. **框架级工程换轨**（study008 结论 4）：数百级特征集（qlib Alpha158 全套 + PIT 财务）+ 非线性模型 + 多频标签——本框架内增量调优已到顶，进一步提升需换框架级工程。
2. **行业质量分层**：成长/制造类行业（汽车/IT/软件/机械）低估后反弹概率高、胜率显著优于价值陷阱类（银行/保险/地产/港口/园区），行业×质量分层选股尚未系统验证。
3. **个股精选回测**：板块策略完成后，在高质量行业内精选 3-5 只个股（用户既定规划）。
4. **独立 OOS 冻结验证**：已预留 2027-2032 独立 OOS 区间，当前所有 ⚠️ 候选结论需在该区间做冻结后验证、补齐可用准入五条后，才可升级为 ✅。
5. **ETF 层深化**：T7 ETF 基线历史上跑赢个股端，纯 ETF 层（低波动/分散）是否比个股层更稳健尚未系统对比。

## 参考

- 基线结论：`STOCK/stock_gbdt_ens_s123_timing.md`（ENS 混合打分 + s123 择时 + V8 避险）
- panel 因子扩充：`STOCK/study008_incremental_enhancements.md`（六条增量路径全否定）
- Alpha101：`STOCK/alpha101_factors.md`
- 筹码/资金流互补：`STOCK/chip_moneyflow_complement.md`
- V5 前视修复：`STOCK/stock_picking_v5_fixed.md`
- 幸存者偏差：`research/sector_rotation/results/survivorship_bias_conclusion.md`
- 代码：`research/sector_rotation/`（`backtest_undervalued_sector_stock.py` 组合/风险层引擎、`backtest_risk_linkage.py` 联动优化、`diag_alpha101_gbdt_wfo.py` / `diag_gbdt_lstm_fusion_wfo.py` / `diag_sentiment_gbdt_wfo.py` 模型级滚动 WFO 诊断、`train_universe_safe_hit30.py` 扩标的池）
