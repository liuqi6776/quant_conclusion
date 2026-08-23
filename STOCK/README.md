# 股票 STOCK

A股股票品类已确认研究成果索引。

| 文件 | 主题 | 状态 |
|------|------|------|
| [stock_composite_ens_risk_im_hedge.md](./stock_composite_ens_risk_im_hedge.md) | 股票综合复合量化策略：全市场 ENS 选股 + S123 三档择时 + 净值降档 + IM 期货低基差对冲 | ✅ 主策略就绪（2019-2026 全期年化 11.80%/回撤-25.48%/夏普0.77；IM对冲β=0.5版年化11.78%/回撤-10.90%/夏普0.94/卡玛1.08） |
| [stock_gbdt_ens_s123_timing.md](./stock_gbdt_ens_s123_timing.md) | 股票 GBDT/ENS 选股 + s123 择时（方案B）：ENS 混合打分中证1000传统行业池月度 Top40 + s123 择时进出 + V8 避险 | ⚠️ 候选（2019-2026 全期年化 11.45%/回撤-30.69%/夏普0.79；无独立 OOS、私有数据、选择过程未控制；个股级 MA5 卖出已证伪） |
| [sector_stock_picking.md](./sector_stock_picking.md) | 板块择时+大盘个股精选：低估池内 PEG40%/筹码25%/ROE15% 全局 Top3 选股，严格 ST/PE/市值/筹码硬过滤 | ⚠️ 候选（2020-2025 全期年化 37.2%/回撤-28.9%/夏普1.45；无独立 OOS、私有数据、选择过程未控制；v5 硬过滤版已证伪） |
| [style_neutralized_index_enhancement.md](./style_neutralized_index_enhancement.md) | 风格中性化指数增强：微观结构因子 + MA20 风控 | ⚠️ 候选（因子 NW 显著；无 OOS、无法回源复现、MaxDD 待回源复核） |
| [option_enhanced_study005.md](./option_enhanced_study005.md) | 期权增强型全局策略 Study 005 | ❌ 已证伪（独立重跑全负，Sharpe 3.08 无法复现） |
| [news_sentiment_prediction.md](./news_sentiment_prediction.md) | 新闻情感与股价预测 | ❌ 已证伪（NW 检验：逐条/每日聚合均不显著） |
| [chip_moneyflow_complement.md](./chip_moneyflow_complement.md) | 筹码边际因子（季频股东户数）与主力资金流互补 | ⚠️ 候选（因子 IC 显著 t=3.92；独立 alpha 温和，建议作过滤因子） |
| [news_sentiment_timing.md](./news_sentiment_timing.md) | 新闻情绪温度计辅助指数增强择时 | 🔬 探索中（方法设计，待回测） |
| [factor_dic_validation.md](./factor_dic_validation.md) | 因子字典（600+）验证策略：日频可验证因子族（流动性/换手/波动/筹码/资金流/羊群） | ⚠️ 候选（统计检验 + 21 因子 IC 层多重检验完成；待冻结后独立 OOS） |
| [turnover_vol_20.md](./turnover_vol_20.md) | 因子提炼：特质换手波动率 turnover_vol_20（候选正交增量因子） | ⚠️ 候选（ICIR 0.750 / t=7.15，21 因子 IC 层已做多重检验；无独立 OOS，完整选择过程未控制，主组合全期跑输基准） |
| [regime_study.md](./regime_study.md) | 市场状态研究：2020~2026 因子×市场分类、RS12 择时 | ⚠️ 候选（描述性研究，供参考） |
| [style_factors.md](./style_factors.md) | 风格因子增量：价值系对主策略贡献（VAL 合成价值 +RS12 年化 16.1%） | ⚠️ 候选（样本内显著增量，无独立 OOS） |
| [alpha101_factors.md](./alpha101_factors.md) | WorldQuant Alpha101 代表因子验证（12 个量价因子对主策略增量） | ❌ 已证伪（月频下无增量，ILLIQ A股反向） |
| [risk_control.md](./risk_control.md) | 回撤控制对比：MA20三档/波动率目标/回撤触发/CPPI-TIPP | ⚠️ 候选（核心逻辑五轮静态审计；2018-2019 风控层跨期支持 oos_scope=component_only；2026-07 快照下 MA20 仅回撤改善成立，收益增强方向反转；完整策略 OOS 未验证、私有数据不可独立复现） |
| [defensive_asset_allocation.md](./defensive_asset_allocation.md) | 多资产避险：RS12 弱段持货基/国债/黄金/混合对比 | ⚠️ 候选（V8 卡玛最优 0.93；单周期 2020~2026，未证跨宏观周期稳健） |
| [study008_incremental_enhancements.md](./study008_incremental_enhancements.md) | study_008 增量增强路径验证：BASE+VAL 4因子基线 + 六条增量路径全否定 + PIT 数据端核验 | ⚠️ 基线候选（年化 14.62%/卡玛 0.55）/ ❌ 六条增量路径全部证伪 / ✅ PIT 数据端核验通过（2026-08-06，工程核验，非策略可用性） |
| [stock_picking_v5_fixed.md](./stock_picking_v5_fixed.md) | 股票精选前视修复审计 + V5-BEST 结论 + Walk-Forward 真实OOS + 牛熊择时验证 + 跨资产配置 | ⚠️ 候选（WF真实OOS 年化7.7%/夏普0.41，跑输ETF；验证集过拟合坐实；牛熊择时（估值+趋势，任意基准）均虚高；跨资产配置 60/40 月频再平衡年化18.5%/回撤-18.4%/夏普1.13 为唯一有效降回撤方向；前视修复已实施；幸存者偏差/换手率口径/ROE覆盖率偏差待检验）/ 旧 V6-S1 37.2% ❌ 已证伪 |
| [growth_direction_exhaustion.md](./growth_direction_exhaustion.md) | 股票 GBDT/ENS 选股增长方向穷举总结：收益层/组合风险层/情绪层增量路线全否定 + 基线锁定 + 剩余方向 | ⚠️ 基线候选（GBDT C8 滚动 WFO ICIR 2.44 天花板）/ ❌ 扩标的池+panel因子+Alpha101+LSTM+联动优化+风险平价+情绪因子全部证伪 / ✅ 幸存者偏差 PIT 核验通过 |
| [post_growth_filter_report.md](./post_growth_filter_report.md) | 成长制造白名单过滤实验全量评估报告：全量指标落盘 + 静态分类偏差 + 行业上限架空机制审计 | 🔬 探索线索（GM_CORE post 14.14% 确认为静态分类后见之明+持仓骤缩至13.6只所致，维持全市场Top40基准） |
| [remediated_audit_report.md](./remediated_audit_report.md) | **量化策略阶段 A 综合整改与独立审计报告**：零标签泄漏 Purged GBDT + 模型消融归因 + A 股微观执行约束 (涨跌停/T+1/费率压测) | ⚠️ **历史指标已作废撤回** (旧 True-ENS 23.41% 与旧 IM 23.54% 存在账本重复计资与全样本筛选缺陷，已正式标记为 Superseded，降级为开发期探索) |
| [expanded_factors_dl_report.md](./expanded_factors_dl_report.md) | **多因子高维扩充 (42特征) 与深度学习 (LSTM/GRU) 综合实证报告**：53 候选因子截面统计筛选 + 42 有效特征 LightGBM 扩容测试 + PyTorch CUDA LSTM/GRU 12个月滑动时序建模 | 🔬 **开发期探索性结果**（全样本特征选择存在测试期重叠，仅作为特征工程参考，不代表独立 OOS） |
| [lambdamart_ranking_report.md](./lambdamart_ranking_report.md) | **排序学习 (LambdaMART / NDCG@40) 损失函数重构实证报告**：从 MSE 均方误差升级为排序学习；Top-40 归一化折损累计增益优化 | 🔬 **探索性负面/风控对照**（回撤显著收敛，但 Rank-Hybrid 实质回退为纯排序） |
| [staggered_tranches_report.md](./staggered_tranches_report.md) | **交错滚动子组合 (Staggered Rolling Tranches) 夏普极值化实证报告**：重叠多子账户周度/双周交错调仓 | 🔬 **探索性平滑线索**（平滑净值曲线，但超额提升有限） |
| [daily_rolling_staggered_report.md](./daily_rolling_staggered_report.md) | **方案 A：高频日级滚动 Alpha 引擎与交错子组合实证报告**：逐日高频微观量价反转 (5d) + 动量加速度 + 低波动收缩 | ❌ **否定实验**（日级量价 Alpha 未能提供独立超额，建议停止继续投入） |
| [leading_crowding_report.md](./leading_crowding_report.md) | **P3 突破实证：前瞻性流动性拥挤度风控研究报告**：筹码顶背离预警 + 换手突变放量滞涨识别 + Amihud 极值过滤 | 🔬 **探索性风控线索**（有效压降波动率，但牺牲收益，需与大类资产协同） |
| [multi_asset_macro_report.md](./multi_asset_macro_report.md) | **P4 突破实证：多资产协同大类配置系统研究报告**：股票 Alpha + IM 期货对冲 + 国债 ETF (511010) + 黄金 ETF (518880) + 银华日利 (511880) | ⚠️ **历史虚高指标已作废** (旧夏普 1.21/1.33 存在本金重复计算与建仓时序缺陷，已被纯净账本重跑数据取代) |
| [remediated_clean_report.md](./remediated_clean_report.md) | **【正式基线】全面量化审计整改与纯净流水线重跑报告**：单一现金池 (零重复计资) + 嵌套样本内特征选择 + 真实 20日 ADV + 停牌禁止交易 + 降档等比减仓 | ✅ **审计通过纯净生产基线**（2023-2026 开发期纯净重跑：纯股票 Alpha 年化 11.12%/夏普 0.45；纯净 IM 对冲年化 11.23%/夏普 0.61/回撤 -28.15%；★ IM 中性对冲多资产年化 6.30%/夏普 0.54/回撤 -10.71%/波动率 7.95%） |




