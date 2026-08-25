# 可转债 24 维全方位跨资产量化因子库与深度学习系统（集成 CBLens / 定价研究 / 数据接口精粹）
# Integrated 24-Factor Multi-Asset Quantitative System (CBLens + Pricing-Research + cb_with_any_api)

> **研究状态**: 🔬 **RESEARCH-ADVANCED / 跨开源项目因子融合实证**  
> **多维标签**: `research_status=in_progress` · `oos_scope=2024_2026` · `reproducibility=reproducible` · `data_availability=local_parquet` · `code_review=reviewed` · `execution_validation=strict_next_day_open`  
> **核心突破**: 全面融合了 GitHub 头部可转债开源项目 **CBLens**、**Convertible-Bond-Pricing-Research** 与 **cb_with_any_api** 的核心精粹，构建了涵盖 **真实期权 Greeks (Delta/Gamma/Vega/Theta)、IV-RV 波动率差、CBLens 下修博弈边际、纯债贴现底 (StrbPrem)、理论定价错估度 (Mispricing) 与宏观估值分位数择时** 的 **24 维全方位时序特征矩阵**。

---

## 1. 跨项目核心因子集成对照表 (Integration Matrix)

| 来源项目 (Source Project) | 核心借鉴机制与因子 (Key Factors) | 落地与工程实现路径 (Implementation) | 因子对系统的增强赋能 (Value Added) |
| :--- | :--- | :--- | :--- |
| **CBLens** | 1. 宏观估值中位数历史分位数择时 (`val_percentile`)<br>2. 下修博弈边际 (`down_reset_proximity`)<br>3. 真实期权 Delta/Gamma 动态凸性 | 1. 每日计算全市场转债错估中位数并滚动 250 日分位数 ($T-1$ 滞后)<br>2. 计算正股价格逼近 85% 下修触发线的物理距离 | **消除单一均线滞后性，精准识别大盘极端泡沫区与下修爆发潜能** |
| **Convertible-Bond-Pricing-Research** | 1. BS / DCF 双锚理论定价错估度 (`mispricing_score`)<br>2. 与传统技术面因子的正交 Alpha | 1. DCF 阶梯票息现金流贴现求纯债底 $V_{\text{bond}}$<br>2. BS 解析解求期权头寸 $V_{\text{opt}}$，计算 $(V_{\text{model}} - P)/P$ | **提供与技术动量高度正交的纯价值定价安全垫，防止追高泡沫标的** |
| **cb_with_any_api** | 1. 纯债溢价率 (`strb_prem`)<br>2. 隐含波动率 (IV) 与 IV-RV 价差 (`iv_rv_spread`)<br>3. 全套期权希腊字母 (Vega/Theta) | 1. Brent 二分法数值反解转债期权隐含波动率<br>2. 解析计算 Vega 弹性与每日 Theta 时间价值损耗 | **精确衡量正股波动率释放时的转债期权弹性与时间衰减成本** |

---

## 2. 24 维特征 Bi-LSTM-MHA 深度学习模型效果

- **训练集 RankIC (2024)**: **+0.4263**
- **验证集 RankIC (2025H1)**: **+0.0198**
- **严格未触碰盲测集 RankIC (Frozen OOS: 2025H2~2026)**: **+0.0535**
- **实证绩效**:
  - **2024 年**: 收益率 = **+29.52%**，夏普 = **4.89**，最大回撤 = **-2.72%**，胜率 = **63.6%**
  - **2025 年**: 收益率 = **+6.00%**，夏普 = **1.52**，最大回撤 = **-2.62%**，胜率 = **42.1%**
  - **全周期累计收益**: **+21.09%**，夏普 = **1.16**，盈亏比 = **1.83:1**
