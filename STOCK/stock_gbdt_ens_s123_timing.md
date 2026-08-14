# 股票 GBDT/ENS 选股 + s123 择时（方案B，quant_system_v2）

> - **来源仓库**：`quant_system_v2`（research/sector_rotation，脚本 `stock_gbdt_s123_backtest.py`）
> - **验证方式**：2019-06 ~ 2026-08 日频状态机回测（月度调仓，无前视）+ 打分源（ENH4/GBDT/ENS）× 持仓（T40/T60）× 卖出（S123_ONLY/IND_MA5）× 择时（S123/ALWAYS）24 组合横向 A/B + target volatility 6 变体
> - **验证区间**：2019-06-03 ~ 2026-08-07（约 7.2 年，1743 个交易日）
> - **数据**：个股 ML 特征面板（72 月，1986 只）+ 中证1000 成分月度快照（PIT，无幸存者偏差）+ 日频行情 + 传统行业映射；双边 20bps（买卖各 10bps）
> - **结论有效期**：量价 + 财务因子的月度选股信号，建议 6-12 个月后复检

## 状态

- **推荐配置 ENS_T40_S123_ONLY_S123（进取版）**: ⚠️ 候选 — 全期正收益显著（年化 11.50%/夏普 0.80，显著优于 ETF 原版 T7 的 6.15%/0.56），但无冻结后独立 OOS、研究选择过程未做多重检验控制、数据为本地私有
  - 多维标签: research_status=validated · code_review=not_reviewed · reproducibility=partial · oos_scope=none · data_availability=private · execution_validation=partial

## 一句话结论

> 在「s123 择时状态机」控制仓位的前提下，用 **ENS 混合打分（0.5×ENH4 秩 + 0.5×GBDT 秩）** 在中证1000 传统行业池内做**月度等权 Top40 精选**（每行业 ≤4 只），组合级 s123 进出、无个股级卖出，资金空闲期进 V8 避险（短债+信用债+黄金等权）：**年化 11.50%、最大回撤 -31.05%（日频口径）/ -23.17%（月频口径）、夏普 0.80、卡玛 0.37**，同风险下明显优于 ETF 原版 T7（年化 6.15%、回撤 -19.03%、夏普 0.56）。与均衡版 ENS_T60_S123_TV12（年化 8.21%、月频回撤 -19.32%≈T7、夏普 0.84）构成「进取/均衡」两档。

## 策略完整设计（四层日频状态机，无前视）

### L1 · s123 择时状态机（月频，定方向）
每月末计算三信号，`s123 = S1 + S2 + S3`，下月首个交易日生效：

| 信号 | 定义 | 触发条件 |
|---|---|---|
| S1 | 沪深300 PE-TTM 10 年滚动分位 | 分位 < 20% |
| S2 | 股债利差 ERP（1/PE_ttm − 10Y 国债）z-score | z-score > 1.0（即 ERP > 均值 + 1σ） |
| S3 | 沪深300 回撤 | 回撤 ≤ −25% |

- **建仓**：`s123 ≥ 3` → 满仓买入 TopN 股票
- **清仓**：`s123 ≤ 1` → 全部转 V8 避险
- **中间态**（2）：维持现状不变（滞回，防频繁进出）

### L2 · 股票池（每月调仓日截面）
中证1000 **当月成分**（PIT 快照，无幸存者偏差）∩ `is_traditional`（传统行业，剔除电子/计算机/传媒/通信/电力设备/国防军工 6 只科技成长 ETF 对应行业）∩ 月成交额 > 1 亿 ∩ 上市 ≥ 60 日。

### L3 · 打分选股（月度截面）
- **ENS 混合打分** = 0.5 × ENH4 秩（pct rank）+ 0.5 × GBDT 秩（pct rank），逐月截面标准化。
- **ENH4（线性）**：`-0.40·ivol − 0.35·ret_1m + 0.15·roe + 0.05·or_yoy + 0.05·netprofit_yoy`（截面 rank 加权）。
- **GBDT（LightGBM 滚动重训）**：
  - 特征集 **C8** = 7 核心（ivol / ret_1m / momentum_20 / volatility_20 / alpha_006 / alpha_012 / enh4_score）+ 3 残差筹码（vwap_20_resid / float_pnl_20_resid / chip_shift_5_resid，先逐月截面 OLS 对基础因子正交取残差、再取负对齐方向）。
  - 参数：`LGBMRegressor(n_estimators=500, lr=0.05, num_leaves=7, max_depth=3, min_child_samples=80, reg_lambda=2.0, reg_alpha=0.1, subsample=0.9, colsample=0.9)` + early_stopping(50)，最后 3 个月作验证集。
  - 滚动重训：预测月 m 只用 ≤ m−1 数据训练；**2023-01 起每月重训，2023 之前用 ENH4 打分填充**（无模型）。
- **行业上限**：`select_with_limit` 每行业最多 4 只（T40），防单行业黑天鹅。

### L4 · 持仓 / 卖出
- **S123_ONLY**：仅组合级 s123 进出，**无个股级 MA5 卖出**（个股级卖出已被证伪，全面劣于 S123_ONLY）。
- 月度再平衡到等权 TopN；无 target volatility 层（进取版特征，区别于均衡版 TV12）。
- 资金空闲期（未建仓 / 清仓后）每日按 V8 增值：**V8 = 511990（短债）1/3 + 511260（信用债）1/3 + 518880（黄金）1/3 等权**。

### 交易约束
- 交易成本：双边 **20bps**（买卖各 10bps，买入 ×1.001 / 卖出 ×0.999）。
- 涨跌停约束：跌停不买（创业板/科创板 0.9 系数、主板 0.95 系数）；100 股整数手。
- 信号时序：T−1 月末收盘算打分与信号，T 日（次月首个交易日）开盘执行，无前视。

## 回测结果（初始 100 万，2019-06 ~ 2026-08）

### 关键组合（ENS 混合打分，v5 口径）

| 版本 | CAGR | MaxDD（日频） | MaxDD（月频） | Calmar | Sharpe |
|---|---|---|---|---|---|
| **★ ENS_T40_S123_ONLY_S123（进取版，推荐）** | **11.50%** | **-31.05%** | **-23.17%** | **0.37** | **0.80** |
| ENS_T60_S123_ONLY_S123 | 11.40% | -30.81% | -22.12% | 0.37 | 0.80 |
| **ENS_T60_S123_TV12（均衡版）** | **8.21%** | **-22.40%** | **-19.32%** | **0.37** | **0.84** |
| ENH_T40_S123_ONLY_S123 | 9.68% | -33.96% | — | 0.29 | 0.69 |
| GBDT_T40_S123_ONLY_S123 | 8.01% | -36.68% | — | 0.22 | 0.59 |
| **ETF 原版 T7（对照）** | **6.15%** | **-19.03%** | — | **0.32** | **0.56** |

> 完整 31 行绩效总表见 `scripts/sector_stock/stock_gbdt_s123_matrix.csv`（24 组合 + 6 TV 变体 + T7）。

### 核心结论
1. **ENS 混合打分是关键增量**：ENS（0.5×ENH4 + 0.5×GBDT）CAGR 11.50% 高于 ENH4 单独 9.68%、GBDT 单独 8.01%，证明 GBDT 提供了 ENH4 没有的增量信息（C8 残差筹码因子 IC 0.0966 首次超越 C7）。
2. **T40 与 T60 几乎无差异**（11.50% vs 11.40%），Top40 略优但差异可忽略。
3. **s123 择时有效**：S123_ONLY 全面优于 ALWAYS（无择时），s123 信号在股票端同样有效（流动性好、无个股暴雷、滑点低）。
4. **个股级 MA5 卖出被证伪**：IND_MA5 各组合 CAGR 仅 4.2%~5.0%（回撤虽降至 -15%~-16%，但收益大幅牺牲），维持废弃。
5. **同风险对标 T7（统一月频口径）**：均衡版 TV12 月频回撤 -19.32% ≈ T7 -19.03%，但 CAGR 8.21% vs 6.15%（+2.1pp），股票方案在相同回撤风险下收益显著占优。

## 复现指引（给 reviewer）

### 代码
- 回测引擎：`research/sector_rotation/stock_gbdt_s123_backtest.py`（本仓库副本 `scripts/sector_stock/stock_gbdt_s123_backtest.py`）
- 结果表：`scripts/sector_stock/stock_gbdt_s123_matrix.csv`
- 结论源文档：`research/sector_rotation/results/stock_gbdt_s123_conclusion.md`（含 v1~v7 完整演进与 Q1~Q9 诊断）

### 数据依赖（本地私有，需向作者索取）
- `D:/iquant_data/data_v2/index_weight/*.parquet` — 中证1000 月度成分快照（PIT）
- `D:/iquant_data/data_v2/data_day1/*.parquet` — 日频 OHLCV 行情
- `research/sector_rotation/stock_ml_panel_72m.parquet` — 个股月度特征面板（72 月，1986 只）
- 行业映射：`research/studies/study_008_enhancements/data/industry_map.parquet`
- 沪深300 PE-TTM / 10Y 国债（s123 信号）与 V8 避险 ETF 日频收益

### 关键数据覆盖率
| 字段 | 覆盖率 | 用途 |
|---|---|---|
| 价量因子（ivol/ret_1m/momentum/volatility/alpha_*） | 100% | 打分 |
| 筹码因子（vwap_20/float_pnl_20/chip_shift_5） | 100% | 残差化后进 GBDT |
| roe / or_yoy / netprofit_yoy | **17%** | ENH4/GBDT 打分（缺失填 sentinel + has_fin 标记） |

## 局限与风险
1. **无独立冻结 OOS**：2019-06 ~ 2026-08 全区间同时用于打分源/持仓/卖出/择时/TV 的多配置选择，GBDT 虽 2023 起滚动重训，但配置选优仍触及测试期数据，存在过拟合与选择偏差风险（`oos_scope=none`）。预留的独立 OOS 区间为 2027-2032。
2. **研究选择过程未做多重检验控制**（FDR / Deflated Sharpe / 冻结验证集），多配置对比中「最好的那个」存在选择偏差。
3. **数据不可独立复现**：私有本地数据，reviewer 无法独立拉取（`reproducibility=partial`）。
4. **执行层部分验证**：已含双边 20bps、涨跌停约束、100 股整数手，但未模拟停牌、容量冲击、滑点、延迟（`execution_validation=partial`）。
5. **财务因子覆盖率仅 17%**：roe/or_yoy/netprofit_yoy 用 sentinel 填充，2023 之前无 GBDT 模型（用 ENH4 打分填充），前期收益主要靠 ENH4 + s123。
6. **回撤口径**：日频口径 MaxDD -31.05%，统一到月频（与 T7 同频）后为 -23.17%；对比时应口径一致。

## 参考
- 完整演进与诊断：`quant_system_v2/research/sector_rotation/results/stock_gbdt_s123_conclusion.md`（v1~v7：特征去冗余 C7→C8、筹码残差化、depth=3 最优、ENS stacking 无增量、GBDT vs DL 方向、回撤口径修正）。
- 相关诊断脚本：`diag_gbdt_features.py` / `diag_gbdt_chip.py` / `diag_ens_as_feature.py` / `diag_ens_t40_drawdown_v5.py` / `diag_drawdown_frequency.py`。
