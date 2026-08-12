# 股票 STOCK

A股股票品类已确认研究成果索引。

| 文件 | 主题 | 状态 |
|------|------|------|
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
| [stock_picking_v5_fixed.md](./stock_picking_v5_fixed.md) | 股票精选前视修复审计 + V5-BEST 结论 | ⚠️ 候选（前视修复已实施；2025半样本外非独立OOS、幸存者偏差/换手率口径/ROE覆盖率偏差待检验）/ 旧 V6-S1 37.2% ❌ 已证伪 |
