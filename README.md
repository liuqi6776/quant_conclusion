# quant_conclusion

已确认（confirmed）的量化交易研究成果库。将各研究仓库中**经过验证/审计的结论**按资产品类归档，避免结论散落在各个仓库中难以检索。

## 状态标记约定

| 标记 | 含义 |
|------|------|
| ✅ 已确认 | 经过 OOS 回测 / 机构级审计 / 严格验证，结论可信 |
| ❌ 已证伪 | 经过验证后确认无效的假设（同样重要，避免重复踩坑） |
| ⚠️ 未验证 | 尚未经过严格验证，仅作参考，**不可直接使用** |

## 品类索引

- [股票 STOCK](./STOCK/README.md)
  - [风格中性化指数增强（final_quant）](./STOCK/style_neutralized_index_enhancement.md)
  - [期权增强型全局策略 Study 005（quant-system）](./STOCK/option_enhanced_study005.md)
  - [新闻情感与股价预测（news_stock_research）](./STOCK/news_sentiment_prediction.md)
- [ETF](./ETF/README.md)
  - [A股ETF期权 Max Pain 研究（quant-research）](./ETF/max_pain_etf_options.md)
- [可转债 CB](./CB/README.md)
  - [可转债双低 PIT 策略研究（CB_research）](./CB/double_low_pit_research.md)

## 使用规则

1. 只有 **✅ 已确认** 的结论可作为策略/因子开发的依据；❌ 和 ⚠️ 仅用于避坑参考。
2. 每个结论文件必须标注：来源仓库、验证方式、验证区间、数据/结论有效期。
3. 新增已确认结论时，先判断品类归属，再在对应目录追加文件，并更新本索引。
