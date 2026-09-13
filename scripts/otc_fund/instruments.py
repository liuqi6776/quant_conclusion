# -*- coding: utf-8 -*-
"""
Fund and Benchmark Instruments Metadata Registry
=================================================
Institutional metadata definitions for all OTC funds, benchmarks, and research proxies.
Enforces strict inception dates, fee tiers, and proxy lineage tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

@dataclass
class InstrumentMeta:
    code: str
    name: str
    asset_class: str
    category: str
    is_qdii: bool
    inception_date: str
    first_available_date: str
    tradable: bool
    sub_fee: float = 0.0015
    red_fee_tiers: List[Tuple[int, float]] = field(default_factory=lambda: [
        (7, 0.015),
        (365, 0.005),
        (730, 0.0025),
        (100000, 0.0)
    ])
    proxy_for: Optional[str] = None
    proxy_start: Optional[str] = None
    proxy_end: Optional[str] = None
    notes: str = ""

# 9 Core Portfolio Funds (True Funds)
CORE_FUNDS: Dict[str, InstrumentMeta] = {
    "000015": InstrumentMeta(
        code="000015",
        name="华夏纯债债券A",
        asset_class="国内纯债",
        category="bond_pure",
        is_qdii=False,
        inception_date="2013-03-08",
        first_available_date="2013-03-08",
        tradable=True,
        notes="优质国内纯债底仓，极低回撤与稳定票息"
    ),
    "004998": InstrumentMeta(
        code="004998",
        name="长信全球债券(QDII)人民币",
        asset_class="全球纯债",
        category="bond_qdii",
        is_qdii=True,
        inception_date="2017-10-10",
        first_available_date="2017-12-11",
        tradable=True,
        notes="全球投资级债券，平抑人民币单一汇率与利率周期"
    ),
    "100032": InstrumentMeta(
        code="100032",
        name="富国中证红利指数增强A",
        asset_class="红利低波",
        category="dividend",
        is_qdii=False,
        inception_date="2008-11-20",
        first_available_date="2008-12-26",
        tradable=True,
        notes="高股息增强，防守型权益底仓"
    ),
    "000198": InstrumentMeta(
        code="000198",
        name="天弘余额宝货币",
        asset_class="现金管理",
        category="money_market",
        is_qdii=False,
        inception_date="2013-05-29",
        first_available_date="2013-05-30",
        tradable=True,
        sub_fee=0.0,
        red_fee_tiers=[(100000, 0.0)],
        notes="流动性现金管理，随时用于逆势补仓"
    ),
    "001917": InstrumentMeta(
        code="001917",
        name="招商量化精选股票A",
        asset_class="A股量化",
        category="quant_a",
        is_qdii=False,
        inception_date="2016-02-18",
        first_available_date="2016-03-15",
        tradable=True,
        notes="A股多因子量化选股，获取稳定Alpha超额"
    ),
    "000216": InstrumentMeta(
        code="000216",
        name="华安黄金易ETF联接A",
        asset_class="现货黄金",
        category="gold",
        is_qdii=False,
        inception_date="2013-08-08",
        first_available_date="2013-08-22",
        tradable=True,
        notes="挂钩上海金交所黄金现货合约，零QDII外汇额度占用"
    ),
    "000834": InstrumentMeta(
        code="000834",
        name="大成纳斯达克100A",
        asset_class="纳指100",
        category="nasdaq",
        is_qdii=True,
        inception_date="2014-11-06",
        first_available_date="2014-11-13",
        tradable=True,
        notes="全球长牛科技指数核心持仓；人民币份额计价（已内生折算USD/CNY汇率），回测假设额度充足"
    ),
    "017730": InstrumentMeta(
        code="017730",
        name="嘉实全球产业升级A",
        asset_class="全球科技",
        category="global_tech",
        is_qdii=True,
        inception_date="2023-01-30",
        first_available_date="2023-02-09",
        tradable=True,
        notes="专注全球AI、半导体与尖端科技产业链；人民币份额计价（已内生折算USD/CNY汇率），回测假设额度充足"
    ),
    "501018": InstrumentMeta(
        code="501018",
        name="南方原油A(QDII-FOF)",
        asset_class="大宗原油",
        category="oil",
        is_qdii=True,
        inception_date="2016-05-17",
        first_available_date="2016-06-15",
        tradable=True,
        notes="大宗商品原油配置，提供尾部抗通胀对冲"
    )
}

# Historical Research Proxies (Used exclusively in proxy asset allocation studies)
RESEARCH_PROXIES: Dict[str, InstrumentMeta] = {
    "000290": InstrumentMeta(
        code="000290",
        name="鹏华全球高收益债(QDII)A",
        asset_class="全球纯债代理",
        category="proxy_bond_qdii",
        is_qdii=True,
        inception_date="2013-10-22",
        first_available_date="2013-10-22",
        tradable=True,
        proxy_for="004998",
        proxy_start="2015-01-05",
        proxy_end="2017-12-10",
        notes="004998 成立前的全球美元高等级/高收益债资产类别代理"
    ),
    "050002": InstrumentMeta(
        code="050002",
        name="博时裕富沪深300指数基金A",
        asset_class="A股大盘/量化代理",
        category="proxy_quant_a",
        is_qdii=False,
        inception_date="2003-08-26",
        first_available_date="2003-08-26",
        tradable=True,
        proxy_for="001917",
        proxy_start="2015-01-05",
        proxy_end="2016-03-14",
        notes="001917 成立前的A股Beta基准代理"
    ),
    "160416": InstrumentMeta(
        code="160416",
        name="华安标普全球石油指数(LOF)A",
        asset_class="大宗原油代理",
        category="proxy_oil",
        is_qdii=True,
        inception_date="2012-03-29",
        first_available_date="2012-03-29",
        tradable=True,
        proxy_for="501018",
        proxy_start="2015-01-05",
        proxy_end="2016-06-14",
        notes="501018 成立前的大宗原油/石油资产类别代理"
    ),
    "000043": InstrumentMeta(
        code="000043",
        name="嘉实美国成长股票(QDII)",
        asset_class="全球科技早期代理",
        category="proxy_global_tech_early",
        is_qdii=True,
        inception_date="2013-06-14",
        first_available_date="2013-06-14",
        tradable=True,
        proxy_for="017730",
        proxy_start="2015-01-05",
        proxy_end="2017-01-24",
        notes="017730 成立前的美国与海外成长科技股代理阶段1"
    ),
    "001668": InstrumentMeta(
        code="001668",
        name="汇添富全球移动互联混合(QDII)A",
        asset_class="全球科技中期代理",
        category="proxy_global_tech_mid",
        is_qdii=True,
        inception_date="2017-01-25",
        first_available_date="2017-01-25",
        tradable=True,
        proxy_for="017730",
        proxy_start="2017-01-25",
        proxy_end="2023-02-09",
        notes="017730 成立前的全球科技/互联网海外基金代理阶段2"
    )
}

# Benchmarks (Indices and Investable Index Funds)
BENCHMARKS: Dict[str, InstrumentMeta] = {
    "sh_index_000001": InstrumentMeta(
        code="000001.SH",
        name="上证综合指数(价格指数)",
        asset_class="市场理论基准",
        category="benchmark_price_index",
        is_qdii=False,
        inception_date="1990-12-19",
        first_available_date="1990-12-19",
        tradable=False,
        sub_fee=0.0,
        red_fee_tiers=[(100000, 0.0)],
        notes="A股市场代表性宏观价格指数（不可直接申购）"
    ),
    "csi300_price_index_000300": InstrumentMeta(
        code="000300.SH",
        name="沪深300指数(价格指数)",
        asset_class="市场理论基准",
        category="benchmark_price_index",
        is_qdii=False,
        inception_date="2005-04-08",
        first_available_date="2005-04-08",
        tradable=False,
        sub_fee=0.0,
        red_fee_tiers=[(100000, 0.0)],
        notes="沪深300大盘代表性价格指数（不可直接申购）"
    ),
    "fund_050002": InstrumentMeta(
        code="050002",
        name="博时裕富沪深300指数基金A",
        asset_class="可投资大盘基准",
        category="benchmark_investable_fund",
        is_qdii=False,
        inception_date="2003-08-26",
        first_available_date="2003-08-26",
        tradable=True,
        sub_fee=0.0015,
        notes="场外可直接申购的沪深300指数基金基准"
    ),
    "csi300_fund_050002": InstrumentMeta(
        code="050002",
        name="博时裕富沪深300指数基金A",
        asset_class="可投资大盘基准",
        category="benchmark_investable_fund",
        is_qdii=False,
        inception_date="2003-08-26",
        first_available_date="2003-08-26",
        tradable=True,
        sub_fee=0.0015,
        notes="场外可直接申购的沪深300指数基金基准（重命名以消除指数与基金混淆）"
    )
}

# Explicit multi-stage lineage for spliced research proxies
PROXY_LINEAGES = {
    "proxy_global_tech": [
        {"stage": 1, "code": "000043", "name": "嘉实美国成长股票(QDII)", "start": "2015-01-05", "end": "2017-01-24"},
        {"stage": 2, "code": "001668", "name": "汇添富全球移动互联混合(QDII)A", "start": "2017-01-25", "end": "2023-02-08"},
        {"stage": 3, "code": "017730", "name": "嘉实全球产业升级A(QDII)", "start": "2023-02-09", "end": "2026-08-06"}
    ],
    "proxy_bond_qdii": [
        {"stage": 1, "code": "000290", "name": "鹏华全球高收益债(QDII)A", "start": "2015-01-05", "end": "2017-12-10"},
        {"stage": 2, "code": "004998", "name": "长信全球债券(QDII)人民币", "start": "2017-12-11", "end": "2026-08-06"}
    ],
    "proxy_quant_a": [
        {"stage": 1, "code": "050002", "name": "博时裕富沪深300指数基金A", "start": "2015-01-05", "end": "2016-03-14"},
        {"stage": 2, "code": "001917", "name": "招商量化精选股票A", "start": "2016-03-15", "end": "2026-08-06"}
    ],
    "proxy_oil": [
        {"stage": 1, "code": "160416", "name": "华安标普全球石油指数(LOF)A", "start": "2015-01-05", "end": "2016-06-14"},
        {"stage": 2, "code": "501018", "name": "南方原油A(QDII-FOF)", "start": "2016-06-15", "end": "2026-08-06"}
    ]
}


# Verified Valid Replacement Funds (Correcting errors such as 001594 bank ETF connect)
REPLACEMENT_RULES = {
    "nasdaq": [
        {"code": "006479", "name": "广发纳斯达克100ETF联接A", "type": "QDII纳指", "status": "valid"},
        {"code": "040046", "name": "华安纳斯达克100ETF联接A", "type": "QDII纳指", "status": "valid"}
    ],
    "global_tech": [
        {"code": "013132", "name": "易方达恒生科技ETF联接A", "type": "港股通科技(0外汇额度)", "status": "valid_proxy"},
        {"code": "012922", "name": "易方达全球成长精选混合C(QDII)", "type": "QDII科技成长", "status": "valid"}
    ],
    "oil": [
        {"code": "161129", "name": "易方达原油A(QDII-FOF)", "type": "QDII原油", "status": "valid"},
        {"code": "162411", "name": "华宝标普油气上游股票(LOF)A", "type": "QDII油气开采股票", "status": "valid_proxy"}
    ],
    "bond_qdii": [
        {"code": "000015", "name": "华夏纯债债券A", "type": "国内纯债置换", "status": "valid_rebalance"}
    ]
}

# Explicit blacklisted mistaken mappings detected in audit
INVALID_MAPPINGS = {
    "001594": "天弘中证银行ETF联接A —— 错误映射！银行指数基金绝不可作为大宗商品原油的平替！"
}

def get_instrument(code: str) -> InstrumentMeta:
    if code in CORE_FUNDS:
        return CORE_FUNDS[code]
    if code in RESEARCH_PROXIES:
        return RESEARCH_PROXIES[code]
    if code in BENCHMARKS:
        return BENCHMARKS[code]
    raise KeyError(f"Instrument with code {code} not registered in metadata registry.")

COLUMN_TO_CODE: Dict[str, str] = {
    "bond_pure_000015": "000015",
    "bond_qdii_004998": "004998",
    "dividend_100032": "100032",
    "money_market_000198": "000198",
    "quant_a_001917": "001917",
    "gold_000216": "000216",
    "nasdaq_000834": "000834",
    "global_tech_017730": "017730",
    "oil_501018": "501018",
    "sh_index_000001": "sh_index_000001",
    "csi300_fund_050002": "050002",
    "fund_050002": "050002",
    "proxy_bond_qdii": "004998",
    "proxy_quant_a": "001917",
    "proxy_oil": "501018",
    "proxy_global_tech": "017730",
}

def resolve_sub_fee(code_or_column: str, default_fee: float = 0.0015) -> float:
    """
    Dynamically resolve statutory subscription fee for an asset column or fund code.
    - 000198 (Money Market): 0.0% statutory subscription fee
    - sh_index_000001 (Theoretical Price Index): 0.0%
    - Registered funds: look up metadata sub_fee
    - Fallback: default_fee (0.0015)
    """
    import re
    # 1. Check exact column-to-code mapping
    lookup_key = COLUMN_TO_CODE.get(code_or_column, code_or_column)
    
    # 2. Try direct instrument lookup
    try:
        return get_instrument(lookup_key).sub_fee
    except KeyError:
        pass
        
    # 3. Exact 6-digit code extraction (avoids arbitrary substring collisions)
    m = re.search(r"(?:^|_)(\d{6})(?:$|_)", code_or_column)
    if m:
        c = m.group(1)
        try:
            return get_instrument(c).sub_fee
        except KeyError:
            pass
            
    return default_fee

