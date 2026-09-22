"""
OmniQuant Strategy Catalog & Academy Knowledge Base
Comprehensive educational metadata for open-source quantitative strategies:
- Theoretical foundation & mathematical formulation
- Best suitable market regimes & conditions
- Advantages, fatal weaknesses, and pitfalls (warning notes)
- Recommended parameter bounds, sensitivity analysis & risk management rules
"""
from typing import Dict, Any, List

STRATEGY_CATALOG: Dict[str, Dict[str, Any]] = {
    "laya_momentum": {
        "id": "laya_momentum",
        "name": "Laya 极速动量风控策略",
        "category": "动量突破与风控",
        "badge": "自研风控核心",
        "tag_color": "emerald",
        "author": "OmniQuant Research",
        "theory_summary": "结合 Wilder RMA 平滑 RSI-14 与双 EMA 趋势通道，在大周期顺势方向捕捉微观动能突破，并在超买钝化或回撤加剧时自适应收缩仓位防守。",
        "math_formula": r"""
1. 相对强弱计算 (Wilder RMA RSI):
   \( U_t = \max(C_t - C_{t-1}, 0), \quad D_t = \max(C_{t-1} - C_t, 0) \)
   \( \bar{U}_t = \frac{\bar{U}_{t-1} \times 13 + U_t}{14}, \quad \bar{D}_t = \frac{\bar{D}_{t-1} \times 13 + D_t}{14} \)
   \( RSI = 100 - \frac{100}{1 + \bar{U}_t / \bar{D}_t} \)
2. 趋势过滤通道:
   \( EMA_{12} = \alpha_{12} C_t + (1 - \alpha_{12}) EMA_{12, t-1} \)
   \( EMA_{26} = \alpha_{26} C_t + (1 - \alpha_{26}) EMA_{26, t-1} \)
3. 决策规则:
   \( \text{多头入场: } (RSI < 35) \lor (EMA_{12} > EMA_{26} \land 48 \le RSI \le 68) \)
   \( \text{空头/离场: } (RSI > 68) \lor (EMA_{12} < EMA_{26} \land RSI < 45) \)
""",
        "suitable_market": "单边上升趋势行情、高动量牛市扩张期、超跌反弹脉冲行情",
        "pros": [
            "双层动量与均线确认，兼具趋势跟随与超跌反弹敏锐度",
            "内置 Wilder RMA 平滑算法，相比标准 SMA RSI 具备更强抗噪能力",
            "在动能衰竭或出现顶部背离形态时能提前收缩敞口防守"
        ],
        "cons": [
            "在长期窄幅横盘无趋势阶段会产生轻度摩擦磨损",
            "极速脉冲行情中可能出现早期止盈从而错过主升浪末期"
        ],
        "default_params": {
            "rsi_period": 14,
            "oversold": 35.0,
            "overbought": 68.0,
            "fast_span": 12,
            "slow_span": 26
        },
        "param_guide": [
            {"param": "rsi_period", "desc": "RSI 平滑周期", "range": "7 - 28", "default": 14, "tip": "周期过短(<7)产生过多假突破；周期过长(>28)信号滞后"},
            {"param": "oversold", "desc": "超跌抄底阈值", "range": "20.0 - 40.0", "default": 35.0, "tip": "激进型可上调至 38，保守型下调至 25-30"},
            {"param": "overbought", "desc": "超买防守阈值", "range": "65.0 - 85.0", "default": 68.0, "tip": "强牛市单边中建议上调至 75-80 避免过早卖飞"}
        ],
        "risk_management_guide": "单笔交易强制止损 3.0% ~ 5.0%，建议搭配 1x ~ 3x 杠杆，禁止在震荡破位区间逆势加仓死扛。"
    },

    "dual_ema": {
        "id": "dual_ema",
        "name": "双均线趋势跟踪策略 (Dual EMA)",
        "category": "趋势跟踪",
        "badge": "经典开源基石",
        "tag_color": "blue",
        "author": "Classic Quant (Backtrader/Freqtrade)",
        "theory_summary": "采用快慢两条指数移动平均线 (EMA) 的交叉作为趋势确立信号。快线上穿慢线形成'黄金交叉'做多，下穿形成'死亡交叉'做空或离场。",
        "math_formula": r"""
\( \alpha = \frac{2}{N + 1} \)
\( EMA_t = \alpha \cdot C_t + (1 - \alpha) \cdot EMA_{t-1} \)
\( \text{买入信号: } EMA_{\text{fast}, t} > EMA_{\text{slow}, t} \land EMA_{\text{fast}, t-1} \le EMA_{\text{slow}, t-1} \)
\( \text{卖出信号: } EMA_{\text{fast}, t} < EMA_{\text{slow}, t} \land EMA_{\text{fast}, t-1} \ge EMA_{\text{slow}, t-1} \)
""",
        "suitable_market": "单边大牛市、大熊市主跌浪（单边持续趋势）",
        "pros": [
            "逻辑清晰优雅，无参数过拟合隐患，长期单边趋势捕获率极高",
            "能够完整吃满长周期趋势的主升浪，盈利无上限"
        ],
        "cons": [
            "【致命盲区】在箱体震荡与锯齿行情中会出现严重的'两头挨巴掌'（Whipsaw 磨损）",
            "滞后性明显，出场点往往位于顶部大幅回撤之后"
        ],
        "default_params": {
            "fast_span": 12,
            "slow_span": 26
        },
        "param_guide": [
            {"param": "fast_span", "desc": "快速均线周期", "range": "5 - 30", "default": 12, "tip": "快线敏感度高，越小开仓越早但也更容易被假突破欺骗"},
            {"param": "slow_span", "desc": "慢速均线周期", "range": "20 - 120", "default": 26, "tip": "慢线代表基准趋势，必须严格大于快线"}
        ],
        "risk_management_guide": "震荡市胜率往往低于 40%，必须依赖 1:3 以上的高盈亏比盈利。务必配合固定止损与追踪止盈，防止单次趋势反转吃掉全部利润。"
    },

    "macd_cross": {
        "id": "macd_cross",
        "name": "MACD 动能共振策略",
        "category": "趋势跟踪",
        "badge": "指标之王",
        "tag_color": "indigo",
        "author": "Gerald Appel (1979) / TA-Lib",
        "theory_summary": "利用快速与慢速平滑异同移动平均线差值 (DIF) 与其信号线 (DEA) 的交叉，结合柱状图 (Hist) 的动能扩张进行趋势确认。",
        "math_formula": r"""
\( DIF_t = EMA_{12}(C) - EMA_{26}(C) \)
\( DEA_t = EMA_9(DIF) \)
\( MACD\_Hist_t = 2 \times (DIF_t - DEA_t) \)
\( \text{多头入场: } DIF_t > DEA_t \land MACD\_Hist_t > 0 \land MACD\_Hist_t > MACD\_Hist_{t-1} \)
\( \text{空头入场: } DIF_t < DEA_t \land MACD\_Hist_t < 0 \)
""",
        "suitable_market": "中长线大波段行情、加速突破阶段",
        "pros": [
            "同时兼顾趋势方向 (DIF) 与价格变化动能加速度 (Hist)",
            "柱状图二次放大往往预示主升浪与主跌浪的爆发节点"
        ],
        "cons": [
            "在超长周期钝化中柱体波动剧烈，产生信号抖动",
            "拐点确认依然存在滞后性"
        ],
        "default_params": {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9
        },
        "param_guide": [
            {"param": "fast_period", "desc": "快线周期", "range": "5 - 20", "default": 12, "tip": "常用 12，加密短期可尝试 8"},
            {"param": "slow_period", "desc": "慢线周期", "range": "20 - 60", "default": 26, "tip": "常用 26，必须远大于快线"},
            {"param": "signal_period", "desc": "信号线平滑周期", "range": "5 - 15", "default": 9, "tip": "平滑信号线周期"}
        ],
        "risk_management_guide": "死叉出现必须无条件平多，杜绝等待'水下金叉'翻本的心态。建议单笔最大亏损控制在总净值的 2% 以内。"
    },

    "supertrend": {
        "id": "supertrend",
        "name": "SuperTrend 超级趋势通道策略",
        "category": "趋势跟踪",
        "badge": "CTA高胜率标配",
        "tag_color": "sky",
        "author": "Olivier Seban (Freqtrade Popular)",
        "theory_summary": "基于真实波幅 (ATR) 动态计算自适应追踪止损带。价格位于通道上方始终保持多头并上移止损线；跌破通道瞬间翻空，完美解决传统均线止损不明确的痛点。",
        "math_formula": r"""
\( TR_t = \max(H_t - L_t, |H_t - C_{t-1}|, |L_t - C_{t-1}|) \)
\( ATR_t = RMA(TR, period) \)
\( \text{基本中轨: } Mid_t = \frac{H_t + L_t}{2} \)
\( \text{上轨: } Upper_t = Mid_t + Multiplier \times ATR_t \)
\( \text{下轨: } Lower_t = Mid_t - Multiplier \times ATR_t \)
\( \text{趋势翻转条件: 价格收盘突破上轨翻多；收盘跌破下轨翻空} \)
""",
        "suitable_market": "单边突破行情、趋势延展行情、高波动牛熊转换期",
        "pros": [
            "动态吸收市场波动率，高波动时自动拉宽止损空间防止被噪音扫损",
            "通道线本身即为移动止损线 (Trailing Stop)，纪律极其严明"
        ],
        "cons": [
            "波动率剧烈收缩转横盘时，通道窄化可能出现连续假突破扫损",
            "插针行情中若触及反转线会强制平仓并反向开仓"
        ],
        "default_params": {
            "atr_period": 10,
            "multiplier": 3.0
        },
        "param_guide": [
            {"param": "atr_period", "desc": "ATR 波动率周期", "range": "7 - 21", "default": 10, "tip": "衡量最近波动的计算窗口"},
            {"param": "multiplier", "desc": "ATR 宽带乘数", "range": "1.5 - 5.0", "default": 3.0, "tip": "乘数越大越不容易被假震荡洗出，但趋势反转时回撤也更大"}
        ],
        "risk_management_guide": "当通道翻转为相反方向时，应直接执行换仓或止损，无需任何主观侥幸心理。"
    },

    "donchian_breakout": {
        "id": "donchian_breakout",
        "name": "海龟交易唐奇安通道突破策略 (Donchian)",
        "category": "趋势跟踪",
        "badge": "海龟交易法则",
        "tag_color": "cyan",
        "author": "Richard Donchian / Turtle Traders (1983)",
        "theory_summary": "传奇海龟交易法则的核心原型。当价格创过去 N 根 K 线的最高价时做多，创过去 N 根 K 线最低价时做空；跌破过去 N/2 根 K 线时止盈出场。",
        "math_formula": r"""
\( Upper\_Band_t = \max(High_{t-1}, High_{t-2}, \dots, High_{t-N}) \)
\( Lower\_Band_t = \min(Low_{t-1}, Low_{t-2}, \dots, Low_{t-N}) \)
\( Exit\_Long_t = \min(Low_{t-1}, \dots, Low_{t-N/2}) \)
\( \text{开多: } Close_t > Upper\_Band_t \)
\( \text{开空: } Close_t < Lower\_Band_t \)
""",
        "suitable_market": "突破历史高点或平台整理突破的爆发性单边大牛市",
        "pros": [
            "绝对不会错过任何一次载入史册的超级单边大行情",
            "纯价格驱动，无任何复杂平滑滞后指标"
        ],
        "cons": [
            "【历史经典痛点】胜率极低（通常仅 30%~38%），绝大多数突破为假突破",
            "需要极其强大的心理承受力面对连续假突破磨损"
        ],
        "default_params": {
            "entry_period": 20,
            "exit_period": 10
        },
        "param_guide": [
            {"param": "entry_period", "desc": "入场突破窗口", "range": "10 - 60", "default": 20, "tip": "经典海龟系统使用 20 与 55 周期"},
            {"param": "exit_period", "desc": "离场平仓窗口", "range": "5 - 30", "default": 10, "tip": "一般为入场周期的 1/2"}
        ],
        "risk_management_guide": "严格按照 ATR (海龟 N 值) 进行头寸缩放 (Position Sizing)，单笔突破头寸风险不得超过总资金的 1.0%。"
    },

    "bollinger": {
        "id": "bollinger",
        "name": "布林带均值回归策略 (Bollinger Bands)",
        "category": "均值回归",
        "badge": "统计套利",
        "tag_color": "amber",
        "author": "John Bollinger (1980s)",
        "theory_summary": "基于正态分布统计学原理，价格有 95.4% 的概率落在均线上下 2 倍标准差区间内。当价格跌破下轨视为超跌统计异常，开多博取向中轨回归。",
        "math_formula": r"""
\( MA_t = \frac{1}{N} \sum_{i=0}^{N-1} C_{t-i} \)
\( \sigma_t = \sqrt{\frac{1}{N} \sum_{i=0}^{N-1} (C_{t-i} - MA_t)^2} \)
\( Upper_t = MA_t + k \cdot \sigma_t, \quad Lower_t = MA_t - k \cdot \sigma_t \)
\( \text{开多: } Close_t < Lower_t \quad (\text{目标: 回归 } MA_t) \)
\( \text{开空: } Close_t > Upper_t \quad (\text{目标: 回归 } MA_t) \)
""",
        "suitable_market": "宽幅箱体震荡、无明显宏观催化的整理行情、高胜率摆动行情",
        "pros": [
            "在震荡市中胜率极高（经常达到 65% ~ 75%）",
            "进出场点位精确，盈亏比边界明确"
        ],
        "cons": [
            "【致命死穴】在遇到单边主升浪或暴跌主跌浪时，价格会'贴着布林带单边破位飞行'，逆势扛单将迅速爆仓"
        ],
        "default_params": {
            "period": 20,
            "std_dev": 2.0
        },
        "param_guide": [
            {"param": "period", "desc": "移动均线周期", "range": "10 - 50", "default": 20, "tip": "经典标准推荐 20"},
            {"param": "std_dev", "desc": "标准差倍数 (k)", "range": "1.5 - 3.0", "default": 2.0, "tip": "加密市场波动剧烈，设置 2.2 ~ 2.5 可滤除更多假触轨"}
        ],
        "risk_management_guide": "均值回归策略【必须设置硬止损】！若价格突破下轨后继续下探超过 3%，必须果断止损，绝不可越跌越买！"
    },

    "rsi_mean_reversion": {
        "id": "rsi_mean_reversion",
        "name": "经典 RSI 极限反转策略",
        "category": "均值回归",
        "badge": "极限超买超卖",
        "tag_color": "yellow",
        "author": "J. Welles Wilder (1978)",
        "theory_summary": "纯摆荡指标策略。监控市场多空超买超卖情绪的极端透支状态，在极度恐慌恐慌盘抛售 (RSI < 25) 时买入，在情绪亢奋贪婪 (RSI > 75) 时了结离场。",
        "math_formula": r"""
\( RSI = 100 - \frac{100}{1 + RS}, \quad RS = \frac{\text{平滑平均涨幅}}{\text{平滑平均跌幅}} \)
\( \text{买入条件: } RSI_t < Oversold\_Level \quad (\text{如 25}) \)
\( \text{平多/做空: } RSI_t > Overbought\_Level \quad (\text{如 75}) \)
""",
        "suitable_market": "震荡市、急速下影线插针行情、洗盘吸筹末期",
        "pros": [
            "捕捉极端情绪反弹效率极高，经常能买在日内或波段的最低点",
            "持仓周期通常较短，资金利用率高"
        ],
        "cons": [
            "在超级大牛市中 RSI 会长达数周在 80 以上'钝化'，若过早做空会被严重逼空",
            "在黑天鹅事件中 RSI 跌破 10 依然可以继续腰斩"
        ],
        "default_params": {
            "rsi_period": 14,
            "oversold": 28.0,
            "overbought": 72.0
        },
        "param_guide": [
            {"param": "rsi_period", "desc": "RSI 周期", "range": "7 - 21", "default": 14, "tip": "短期可用 7 (灵敏)，稳健用 14"},
            {"param": "oversold", "desc": "超卖阈值", "range": "15.0 - 35.0", "default": 28.0, "tip": "越低越安全，但信号频率越低"},
            {"param": "overbought", "desc": "超买阈值", "range": "65.0 - 85.0", "default": 72.0, "tip": "建议配合量能配合"}
        ],
        "risk_management_guide": "必须设置时间止损或价格硬止损（如 3 根 K 线内不反弹立即离场），谨防单边流动性枯竭断崖崩盘。"
    },

    "keltner_channel": {
        "id": "keltner_channel",
        "name": "肯特纳通道平滑回归策略 (Keltner Channels)",
        "category": "均值回归",
        "badge": "抗假突破通道",
        "tag_color": "teal",
        "author": "Chester Keltner (1960) / Linda Raschke",
        "theory_summary": "与布林带类似但采用真实波幅 ATR 而非标准差构建通道宽度，中轨采用 EMA 平滑。相比布林带，肯特纳通道更加平滑，能有效滤除高波动市场的瞬时插针噪音。",
        "math_formula": r"""
\( Mid_t = EMA_{20}(Close) \)
\( Upper_t = Mid_t + Multiplier \times ATR_{10} \)
\( Lower_t = Mid_t - Multiplier \times ATR_{10} \)
\( \text{多头入场: } Close_t < Lower_t \land Close_{t-1} \ge Lower_{t-1} \text{ 或突破回踩} \)
\( \text{多头止盈: } Close_t \ge Mid_t \)
""",
        "suitable_market": "温和震荡市、均线多头排列中的回调回踩点",
        "pros": [
            "通道宽度反映真实交易跨度，不会因为单根异常大阳线导致通道瞬间畸形膨胀",
            "信号稳健度高于布林带，假突破率低"
        ],
        "cons": [
            "在波动率突变极度剧烈时通道扩张偏慢",
            "信号触发频率相对布林带较少"
        ],
        "default_params": {
            "ema_period": 20,
            "atr_period": 10,
            "multiplier": 2.0
        },
        "param_guide": [
            {"param": "ema_period", "desc": "中轨均线周期", "range": "10 - 40", "default": 20, "tip": "基准均线周期"},
            {"param": "atr_period", "desc": "ATR 周期", "range": "7 - 20", "default": 10, "tip": "波动率周期"},
            {"param": "multiplier", "desc": "通道宽度乘数", "range": "1.5 - 3.0", "default": 2.0, "tip": "乘数越大越宽"}
        ],
        "risk_management_guide": "跌破下轨开多后，若继续下挫跌破 1.5 倍 ATR 距离必须无条件止损。"
    },

    "stoch_rsi": {
        "id": "stoch_rsi",
        "name": "随机相对强弱指标策略 (StochRSI)",
        "category": "均值回归",
        "badge": "高频灵敏摆荡",
        "tag_color": "violet",
        "author": "Tushar Chande & Stanley Kroll (1994)",
        "theory_summary": "对 RSI 指标再次进行随机震荡指标 (Stochastic) 计算，测量当前 RSI 相对于其在指定周期内高低点的位置，大幅提高了摆荡指标对转折点的反应速度。",
        "math_formula": r"""
\( StochRSI = \frac{RSI_t - \min(RSI, n)}{\max(RSI, n) - \min(RSI, n)} \)
\( \%K = SMA(StochRSI, 3), \quad \%D = SMA(\%K, 3) \)
\( \text{金叉做多: } \%K \text{ 上穿 } \%D \land \%K < 0.2 \)
\( \text{死叉平多: } \%K \text{ 下穿 } \%D \land \%K > 0.8 \)
""",
        "suitable_market": "日内短周期微波、窄幅震荡抢反弹、波段高抛低吸",
        "pros": [
            "极度灵敏，比普通 RSI 快 1~2 根 K 线发出转折预警",
            "明确量化 0.0 ~ 1.0 的超买超卖边界"
        ],
        "cons": [
            "因为极度灵敏，在强趋势中可能产生过多虚假交叉信号",
            "不适合单独作为长周期决策依据，需搭配均线趋势过滤"
        ],
        "default_params": {
            "rsi_period": 14,
            "stoch_period": 14,
            "k_period": 3,
            "d_period": 3
        },
        "param_guide": [
            {"param": "rsi_period", "desc": "基础 RSI 周期", "range": "7 - 21", "default": 14, "tip": "基础平滑周期"},
            {"param": "stoch_period", "desc": "随机窗口周期", "range": "7 - 21", "default": 14, "tip": "用于计算 RSI 极值窗口"}
        ],
        "risk_management_guide": "由于信号频率极高，切勿频繁操作导致交易手续费侵蚀利润。务必设定硬性滑点与手续费扣除。"
    },

    "volatility_squeeze": {
        "id": "volatility_squeeze",
        "name": "TTM Squeeze 波动率挤压突破策略",
        "category": "波动率突破",
        "badge": "主升浪捕捉利器",
        "tag_color": "rose",
        "author": "John Carter (Mastering the Trade)",
        "theory_summary": "基于'波动率周期性由低向高循环'的物理定律。当布林带完全收敛进肯特纳通道内部时，代表市场处于极度变盘前夕的'挤压 (Squeeze)'蓄力状态；一旦布林带冲破肯特纳通道并伴随动能爆发，即为主升浪/主跌浪启动信号。",
        "math_formula": r"""
\( \text{Squeeze 触发: } Bollinger\_Upper < Keltner\_Upper \land Bollinger\_Lower > Keltner\_Lower \)
\( \text{Squeeze 释放 (Fire): } \text{布林带重新扩张突破肯特纳通道} \)
\( \text{动能方向判定: 基于线性回归去趋势价格振幅或 MACD 动能判定方向} \)
\( \text{买入: Squeeze 释放 且 动量指标 > 0 且 递增} \)
""",
        "suitable_market": "长时间窄幅横盘后的爆发性方向选择、重大事件/数据发布前的变盘突破",
        "pros": [
            "专注于高赔率的爆发性行情，过滤掉了大部分垃圾无效交易时间",
            "主升浪起爆点抓取成功率极高"
        ],
        "cons": [
            "长期蓄势期间完全没有交易信号（空仓等待时间较长）",
            "遇上假突破诱多/诱空时回撤较快"
        ],
        "default_params": {
            "bb_period": 20,
            "bb_std": 2.0,
            "kc_period": 20,
            "kc_mult": 1.5
        },
        "param_guide": [
            {"param": "bb_period", "desc": "布林带周期", "range": "15 - 30", "default": 20, "tip": "挤压窗口"},
            {"param": "kc_mult", "desc": "肯特纳通道倍数", "range": "1.0 - 2.0", "default": 1.5, "tip": "越小更容易触发挤压"}
        ],
        "risk_management_guide": "爆发突破入场后，若 2 根 K 线内收回挤压带内部，表明为假突破，必须立即止损离场！"
    },

    "dual_thrust": {
        "id": "dual_thrust",
        "name": "Dual Thrust 经典日内自适应突破策略",
        "category": "波动率突破",
        "badge": "CTA量化常青树",
        "tag_color": "orange",
        "author": "Michael Chalek (CTA Classical)",
        "theory_summary": "期货 CTA 领域最负盛名的日内趋势突破系统。通过前 N 日的最高价、最低价与收盘价加权计算出动态非对称区间 Range，叠加在今日开盘价之上形成上下突破触发线。",
        "math_formula": r"""
\( Range = \max(HH - LC, HC - LL) \)
\( \text{上轨: } Buy\_Line = Open_t + K_1 \times Range \)
\( \text{下轨: } Sell\_Line = Open_t - K_2 \times Range \)
\( \text{开多: } Price > Buy\_Line, \quad \text{开空: } Price < Sell\_Line \)
""",
        "suitable_market": "日内大幅单边震荡推升或下泻、大阳线加速日",
        "pros": [
            "非对称系数 K1 与 K2 可以针对加密市场牛多熊急特性灵活设定多空偏好",
            "逻辑坚固，历经几十年全球期货与外汇市场实盘检验"
        ],
        "cons": [
            "在早盘冲高回落的'倒锤子线'行情中容易被套在最高点",
            "需要明确的开盘基准锚点"
        ],
        "default_params": {
            "period": 5,
            "k1": 0.5,
            "k2": 0.5
        },
        "param_guide": [
            {"param": "period", "desc": "历史窗口天数", "range": "3 - 10", "default": 5, "tip": "衡量近期振幅的天数"},
            {"param": "k1", "desc": "做多突破系数", "range": "0.3 - 1.0", "default": 0.5, "tip": "值越小越敏感"},
            {"param": "k2", "desc": "做空突破系数", "range": "0.3 - 1.0", "default": 0.5, "tip": "做空触发阈值"}
        ],
        "risk_management_guide": "突破开仓后必须将止损设在开盘价 (Open) 或反向轨，防止冲高反杀造成大幅亏损。"
    },

    "mfi_divergence": {
        "id": "mfi_divergence",
        "name": "MFI 资金流量指标量价背离策略",
        "category": "资金流量价",
        "badge": "主力资金异动",
        "tag_color": "purple",
        "author": "Gene Quong & Avrum Soudack (TA-Lib)",
        "theory_summary": "被称为'成交量加权版的 RSI'。不仅看价格高低，更将每笔交易的典型价格与成交量乘积（资金流 Money Flow）纳入计算。当价格创新低而 MFI 拒绝创新低时，代表主力正在暗中吸筹（底背离）。",
        "math_formula": r"""
\( Typical\_Price_t = \frac{High_t + Low_t + Close_t}{3} \)
\( Raw\_Money\_Flow_t = Typical\_Price_t \times Volume_t \)
\( \text{正向资金流 (如果 } TP_t > TP_{t-1} \text{)}: PMF = \sum RawMF \)
\( \text{负向资金流 (如果 } TP_t < TP_{t-1} \text{)}: NMF = \sum RawMF \)
\( MFI = 100 - \frac{100}{1 + PMF / NMF} \)
\( \text{底背离做多: 价格新低 但 } MFI > 20 \text{ 且金叉回升} \)
""",
        "suitable_market": "洗盘筑底阶段、量价背离转折点、假跌破真反弹节点",
        "pros": [
            "有效揭示无量空跌与放量滞涨，识破没有量能支撑的虚假诱空",
            "将成交量真实引入动量分析，维度比纯价格指标丰富"
        ],
        "cons": [
            "在某些交易所 API 刷量严重时，成交量失真会误导 MFI 计算",
            "需要稳定可靠的 Tick 级真实交易量数据支持"
        ],
        "default_params": {
            "mfi_period": 14,
            "oversold": 20.0,
            "overbought": 80.0
        },
        "param_guide": [
            {"param": "mfi_period", "desc": "资金流计算周期", "range": "10 - 28", "default": 14, "tip": "平滑窗口"},
            {"param": "oversold", "desc": "超卖阈值", "range": "15.0 - 25.0", "default": 20.0, "tip": "极度资金流净流出"},
            {"param": "overbought", "desc": "超买阈值", "range": "75.0 - 85.0", "default": 80.0, "tip": "极度资金流亢奋"}
        ],
        "risk_management_guide": "量价背离往往发生在逆势左侧，必须轻仓试仓（不超过 10% 仓位），右侧确立放量大阳线后再行加仓。"
    }
}
