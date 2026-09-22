"""
OmniQuant Crypto Strategy Library (Full Classical Suite & Custom Rule Builder)
Contains 12+ industry-standard quantitative trading strategies and a custom rule execution engine:
1. LayaMomentumStrategy: Laya adaptive momentum with Wilder RMA RSI & EMA
2. DualEMAStrategy: Fast & Slow Exponential Moving Average trend following
3. MACDCrossStrategy: MACD signal line crossover & histogram expansion
4. SuperTrendStrategy: ATR-based adaptive trailing stop channel
5. DonchianBreakoutStrategy: Turtle Trader 20-bar breakout system
6. BollingerBandsStrategy: 2.0-sigma statistical mean reversion
7. RSIMeanReversionStrategy: Wilder RSI extreme exhaustion reversal
8. KeltnerChannelStrategy: Smooth EMA + ATR channel mean reversion
9. StochRSIStrategy: High-frequency Stochastic RSI oscillator
10. VolatilitySqueezeStrategy: TTM Squeeze volatility contraction/expansion
11. DualThrustStrategy: Michael Chalek classic CTA range breakout
12. MFIDivergenceStrategy: Money Flow Index volume-weighted momentum
13. CustomRuleStrategy: Dynamic user-configured quantitative rule engine
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from data.feature_engine import FeatureEngine
from backtest.strategy_catalog import STRATEGY_CATALOG

class BaseStrategy(ABC):
    name: str = "BaseStrategy"
    description: str = "Base Strategy Description"
    category: str = "通用"

    def __init__(self, params: Dict[str, Any] = None):
        self.params = params or {}

    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        """
        根据历史 K 线数据生成交易信号:
        +1: 做多 (BUY / LONG)
        -1: 做空 (SELL / SHORT)
         0: 空仓或保持 (HOLD / EXIT)
        """
        pass

# ================= 1. Laya 极速动量风控策略 =================
class LayaMomentumStrategy(BaseStrategy):
    name = "Laya 极速动量风控策略"
    description = "集成 Wilder RMA RSI-14 与 EMA 双通道动量过滤，兼具自适应止盈防守机制"
    category = "动量突破与风控"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        rsi_period = int(self.params.get("rsi_period", 14))
        oversold = float(self.params.get("oversold", 35.0))
        overbought = float(self.params.get("overbought", 68.0))

        rsi = FeatureEngine.calculate_rsi_series(close, period=rsi_period)
        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()

        signals = pd.Series(0, index=df.index, dtype=int)
        buy_cond = (rsi < oversold) | ((ema_fast > ema_slow) & (rsi >= 48) & (rsi <= overbought))
        sell_cond = (rsi > overbought) | ((ema_fast < ema_slow) & (rsi < 45))

        signals[buy_cond] = 1
        signals[sell_cond] = -1
        return signals

# ================= 2. 双均线趋势跟踪策略 =================
class DualEMAStrategy(BaseStrategy):
    name = "双均线趋势跟踪策略"
    description = "经典快速与慢速指数移动平均线交叉趋势跟踪系统"
    category = "趋势跟踪"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast_span = int(self.params.get("fast_span", 12))
        slow_span = int(self.params.get("slow_span", 26))

        close = df["close"]
        fast_ema = close.ewm(span=fast_span, adjust=False).mean()
        slow_ema = close.ewm(span=slow_span, adjust=False).mean()

        signals = pd.Series(0, index=df.index, dtype=int)
        signals[fast_ema > slow_ema] = 1
        signals[fast_ema < slow_ema] = -1
        return signals

# ================= 3. MACD 动能共振策略 =================
class MACDCrossStrategy(BaseStrategy):
    name = "MACD 动能共振策略"
    description = "DIF 与 DEA 双线交叉配合柱状图动能扩张的经典波段趋势系统"
    category = "趋势跟踪"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        fast = int(self.params.get("fast_period", 12))
        slow = int(self.params.get("slow_period", 26))
        signal_p = int(self.params.get("signal_period", 9))

        close = df["close"]
        ema_fast = close.ewm(span=fast, adjust=False).mean()
        ema_slow = close.ewm(span=slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=signal_p, adjust=False).mean()
        hist = 2.0 * (dif - dea)

        signals = pd.Series(0, index=df.index, dtype=int)
        # 金叉且柱体为正
        signals[(dif > dea) & (hist > 0)] = 1
        # 死叉且柱体为负
        signals[(dif < dea) & (hist < 0)] = -1
        return signals

# ================= 4. SuperTrend 超级趋势通道策略 =================
class SuperTrendStrategy(BaseStrategy):
    name = "SuperTrend 超级趋势通道策略"
    description = "基于真实波幅 ATR 的自适应动态跟踪止损通道，趋势翻转果断"
    category = "趋势跟踪"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        atr_period = int(self.params.get("atr_period", 10))
        multiplier = float(self.params.get("multiplier", 3.0))

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # 计算 ATR
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0 / atr_period, adjust=False).mean()

        hl2 = (high + low) / 2.0
        upper_band = hl2 + (multiplier * atr)
        lower_band = hl2 - (multiplier * atr)

        n = len(df)
        signals = pd.Series(0, index=df.index, dtype=int)
        trend = np.zeros(n, dtype=int)
        trail_upper = np.zeros(n, dtype=float)
        trail_lower = np.zeros(n, dtype=float)

        trail_upper[0] = upper_band.iloc[0]
        trail_lower[0] = lower_band.iloc[0]
        trend[0] = 1 if close.iloc[0] > trail_upper[0] else -1

        for i in range(1, n):
            c = close.iloc[i]
            c_prev = close.iloc[i-1]
            u = upper_band.iloc[i]
            l = lower_band.iloc[i]

            # 动态调整上下轨
            trail_lower[i] = l if (l > trail_lower[i-1] or c_prev < trail_lower[i-1]) else trail_lower[i-1]
            trail_upper[i] = u if (u < trail_upper[i-1] or c_prev > trail_upper[i-1]) else trail_upper[i-1]

            if trend[i-1] == 1:
                trend[i] = -1 if c < trail_lower[i] else 1
            else:
                trend[i] = 1 if c > trail_upper[i] else -1

        signals = pd.Series(trend, index=df.index)
        return signals

# ================= 5. 海龟交易唐奇安通道突破策略 =================
class DonchianBreakoutStrategy(BaseStrategy):
    name = "海龟交易唐奇安通道突破策略"
    description = "突破 N 周期高点开多，跌破 N 周期低点开空的传奇海龟交易法则"
    category = "趋势跟踪"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        entry_p = int(self.params.get("entry_period", 20))
        exit_p = int(self.params.get("exit_period", 10))

        high = df["high"]
        low = df["low"]
        close = df["close"]

        # 上轨: 过去 entry_p 根 K 线的最高价 (不含当前根)
        upper = high.shift(1).rolling(window=entry_p).max()
        lower = low.shift(1).rolling(window=entry_p).min()
        exit_lower = low.shift(1).rolling(window=exit_p).min()
        exit_upper = high.shift(1).rolling(window=exit_p).max()

        signals = pd.Series(0, index=df.index, dtype=int)
        pos = 0
        sig_arr = np.zeros(len(df), dtype=int)

        for i in range(len(df)):
            c = close.iloc[i]
            u = upper.iloc[i]
            l = lower.iloc[i]
            ex_l = exit_lower.iloc[i]
            ex_u = exit_upper.iloc[i]

            if pd.isna(u) or pd.isna(l):
                sig_arr[i] = 0
                continue

            if pos == 0:
                if c > u:
                    pos = 1
                elif c < l:
                    pos = -1
            elif pos == 1:
                if c < ex_l:
                    pos = 0 # 触发离场
                elif c < l:
                    pos = -1 # 反转做空
            elif pos == -1:
                if c > ex_u:
                    pos = 0 # 触发离场
                elif c > u:
                    pos = 1 # 反转做多

            sig_arr[i] = pos

        signals = pd.Series(sig_arr, index=df.index)
        return signals

# ================= 6. 布林带均值回归策略 =================
class BollingerBandsStrategy(BaseStrategy):
    name = "布林带均值回归策略"
    description = "基于统计学 2 倍标准差上下轨道的统计套利与触轨反转策略"
    category = "均值回归"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        period = int(self.params.get("period", 20))
        std_dev = float(self.params.get("std_dev", 2.0))

        close = df["close"]
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()
        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        signals = pd.Series(0, index=df.index, dtype=int)
        # 跌破下轨买入做多
        signals[close < lower] = 1
        # 突破上轨卖出平仓或做空
        signals[close > upper] = -1
        return signals

# ================= 7. 经典 RSI 极限反转策略 =================
class RSIMeanReversionStrategy(BaseStrategy):
    name = "经典 RSI 极限反转策略"
    description = "监控市场极度恐慌与极度贪婪情绪，在极值点捕捉高胜率波段反弹"
    category = "均值回归"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        period = int(self.params.get("rsi_period", 14))
        oversold = float(self.params.get("oversold", 28.0))
        overbought = float(self.params.get("overbought", 72.0))

        close = df["close"]
        rsi = FeatureEngine.calculate_rsi_series(close, period=period)

        signals = pd.Series(0, index=df.index, dtype=int)
        signals[rsi < oversold] = 1
        signals[rsi > overbought] = -1
        return signals

# ================= 8. 肯特纳通道平滑回归策略 =================
class KeltnerChannelStrategy(BaseStrategy):
    name = "肯特纳通道平滑回归策略"
    description = "以 EMA 为中轨、ATR 为带宽的平滑通道，比布林带更抗极端插针假突破"
    category = "均值回归"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        ema_p = int(self.params.get("ema_period", 20))
        atr_p = int(self.params.get("atr_period", 10))
        multiplier = float(self.params.get("multiplier", 2.0))

        close = df["close"]
        high = df["high"]
        low = df["low"]

        ema = close.ewm(span=ema_p, adjust=False).mean()
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0 / atr_p, adjust=False).mean()

        upper = ema + (multiplier * atr)
        lower = ema - (multiplier * atr)

        signals = pd.Series(0, index=df.index, dtype=int)
        signals[close < lower] = 1
        signals[close > upper] = -1
        return signals

# ================= 9. 随机相对强弱指标策略 (StochRSI) =================
class StochRSIStrategy(BaseStrategy):
    name = "随机相对强弱指标策略 (StochRSI)"
    description = "测量 RSI 在指定周期高低点区间的敏感摆荡指标，超前捕捉拐点"
    category = "均值回归"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        rsi_p = int(self.params.get("rsi_period", 14))
        stoch_p = int(self.params.get("stoch_period", 14))

        close = df["close"]
        rsi = FeatureEngine.calculate_rsi_series(close, period=rsi_p)
        min_rsi = rsi.rolling(window=stoch_p).min()
        max_rsi = rsi.rolling(window=stoch_p).max()

        denom = (max_rsi - min_rsi).replace(0, np.nan)
        stoch_rsi = (rsi - min_rsi) / denom
        stoch_rsi = stoch_rsi.fillna(0.5)

        k = stoch_rsi.rolling(window=3).mean()
        d = k.rolling(window=3).mean()

        signals = pd.Series(0, index=df.index, dtype=int)
        # 超卖区金叉开多
        signals[(k > d) & (k < 0.25)] = 1
        # 超买区死叉开空
        signals[(k < d) & (k > 0.75)] = -1
        return signals

# ================= 10. TTM Squeeze 波动率挤压突破策略 =================
class VolatilitySqueezeStrategy(BaseStrategy):
    name = "TTM Squeeze 波动率挤压突破策略"
    description = "监控布林带完全进入肯特纳通道的极度蓄势阶段，在释放瞬间追击主升浪"
    category = "波动率突破"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        bb_p = int(self.params.get("bb_period", 20))
        bb_std = float(self.params.get("bb_std", 2.0))
        kc_p = int(self.params.get("kc_period", 20))
        kc_mult = float(self.params.get("kc_mult", 1.5))

        close = df["close"]
        high = df["high"]
        low = df["low"]

        # 布林带
        sma = close.rolling(window=bb_p).mean()
        std = close.rolling(window=bb_p).std()
        bb_upper = sma + (std * bb_std)
        bb_lower = sma - (std * bb_std)

        # 肯特纳通道
        ema = close.ewm(span=kc_p, adjust=False).mean()
        tr = pd.concat([high - low, (high - close.shift(1)).abs(), (low - close.shift(1)).abs()], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1.0 / kc_p, adjust=False).mean()
        kc_upper = ema + (kc_mult * atr)
        kc_lower = ema - (kc_mult * atr)

        # Squeeze 状态: 布林带完全在肯特纳通道内部
        squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)
        squeeze_fired = (squeeze_on.shift(1) == True) & (squeeze_on == False)

        # 动能判定 (差值动量)
        momentum = close - sma

        signals = pd.Series(0, index=df.index, dtype=int)
        # 释放且向上突破
        signals[squeeze_fired & (momentum > 0)] = 1
        # 释放且向下突破
        signals[squeeze_fired & (momentum < 0)] = -1

        # 持仓延续：如果处于释放后且动量同向，保持信号
        sig_arr = signals.to_numpy(copy=True)
        pos = 0
        for i in range(len(sig_arr)):
            if sig_arr[i] != 0:
                pos = sig_arr[i]
            elif pos != 0:
                # 动量反向时离场
                if (pos == 1 and momentum.iloc[i] < 0) or (pos == -1 and momentum.iloc[i] > 0):
                    pos = 0
            sig_arr[i] = pos

        return pd.Series(sig_arr, index=df.index)

# ================= 11. Dual Thrust 经典日内区间自适应突破策略 =================
class DualThrustStrategy(BaseStrategy):
    name = "Dual Thrust 经典日内突破策略"
    description = "基于前 N 日加权波动区间构建非对称上下轨，期货 CTA 领域经典突破系统"
    category = "波动率突破"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        period = int(self.params.get("period", 5))
        k1 = float(self.params.get("k1", 0.5))
        k2 = float(self.params.get("k2", 0.5))

        high = df["high"]
        low = df["low"]
        close = df["close"]
        open_p = df["open"]

        hh = high.shift(1).rolling(window=period).max()
        lc = close.shift(1).rolling(window=period).min()
        hc = close.shift(1).rolling(window=period).max()
        ll = low.shift(1).rolling(window=period).min()

        range_val = pd.concat([hh - lc, hc - ll], axis=1).max(axis=1)
        buy_line = open_p + (k1 * range_val)
        sell_line = open_p - (k2 * range_val)

        signals = pd.Series(0, index=df.index, dtype=int)
        signals[close > buy_line] = 1
        signals[close < sell_line] = -1
        return signals

# ================= 12. MFI 资金流量指标量价背离策略 =================
class MFIDivergenceStrategy(BaseStrategy):
    name = "MFI 资金流量指标量价背离策略"
    description = "成交量加权动量分析，识破虚假诱空并在主力资金暗中吸筹时果断入场"
    category = "资金流量价"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        period = int(self.params.get("mfi_period", 14))
        oversold = float(self.params.get("oversold", 20.0))
        overbought = float(self.params.get("overbought", 80.0))

        high = df["high"]
        low = df["low"]
        close = df["close"]
        volume = df["volume"]

        typical_price = (high + low + close) / 3.0
        raw_money_flow = typical_price * volume

        pos_flow = pd.Series(0.0, index=df.index)
        neg_flow = pd.Series(0.0, index=df.index)

        price_diff = typical_price.diff()
        pos_flow[price_diff > 0] = raw_money_flow[price_diff > 0]
        neg_flow[price_diff < 0] = raw_money_flow[price_diff < 0]

        pos_sum = pos_flow.rolling(window=period).sum()
        neg_sum = neg_flow.rolling(window=period).sum()

        money_ratio = pos_sum / (neg_sum.replace(0, np.nan))
        mfi = 100.0 - (100.0 / (1.0 + money_ratio))
        mfi = mfi.fillna(50.0)

        signals = pd.Series(0, index=df.index, dtype=int)
        # 极端资金流低点金叉向上
        signals[(mfi < oversold) | ((mfi.shift(1) < oversold) & (mfi > oversold))] = 1
        signals[(mfi > overbought) | ((mfi.shift(1) > overbought) & (mfi < overbought))] = -1
        return signals

# ================= 13. 自定义规则策略引擎 (CustomRuleStrategy) =================
class CustomRuleStrategy(BaseStrategy):
    """
    用户通过自定义策略工坊生成的结构化规则执行引擎:
    支持用户自由组合指标、设置入场条件与强制风控规则
    """
    name = "自定义规则策略"
    description = "用户在自定义策略工坊中个性化构建的量化规则模型"
    category = "自定义复合"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        high = df["high"]
        low = df["low"]
        vol = df["volume"]

        indicators = self.params.get("indicators", {})
        entry_rules = self.params.get("entry_rules", {})

        # 计算所选指标
        ind_data = {}

        if "rsi" in indicators:
            cfg = indicators["rsi"]
            ind_data["rsi"] = FeatureEngine.calculate_rsi_series(close, period=int(cfg.get("period", 14)))
            ind_data["rsi_oversold"] = float(cfg.get("oversold", 30.0))
            ind_data["rsi_overbought"] = float(cfg.get("overbought", 70.0))

        if "ema" in indicators:
            cfg = indicators["ema"]
            f_span = int(cfg.get("fast_period", 12))
            s_span = int(cfg.get("slow_period", 26))
            ind_data["ema_fast"] = close.ewm(span=f_span, adjust=False).mean()
            ind_data["ema_slow"] = close.ewm(span=s_span, adjust=False).mean()

        if "bollinger" in indicators:
            cfg = indicators["bollinger"]
            bb_p = int(cfg.get("period", 20))
            bb_s = float(cfg.get("std_dev", 2.0))
            sma = close.rolling(window=bb_p).mean()
            std = close.rolling(window=bb_p).std()
            ind_data["bb_mid"] = sma
            ind_data["bb_upper"] = sma + (std * bb_s)
            ind_data["bb_lower"] = sma - (std * bb_s)

        if "macd" in indicators:
            cfg = indicators["macd"]
            mf = int(cfg.get("fast_period", 12))
            ms = int(cfg.get("slow_period", 26))
            msig = int(cfg.get("signal_period", 9))
            dif = close.ewm(span=mf, adjust=False).mean() - close.ewm(span=ms, adjust=False).mean()
            dea = dif.ewm(span=msig, adjust=False).mean()
            ind_data["macd_dif"] = dif
            ind_data["macd_dea"] = dea
            ind_data["macd_hist"] = 2.0 * (dif - dea)

        long_cond_str = entry_rules.get("long_condition", "NONE")
        short_cond_str = entry_rules.get("short_condition", "NONE")

        signals = pd.Series(0, index=df.index, dtype=int)
        buy_mask = pd.Series(False, index=df.index)
        sell_mask = pd.Series(False, index=df.index)

        # 解析多头条件
        if long_cond_str == "EMA_GOLDEN_CROSS" and "ema_fast" in ind_data:
            buy_mask = (ind_data["ema_fast"] > ind_data["ema_slow"]) & (ind_data["ema_fast"].shift(1) <= ind_data["ema_slow"].shift(1))
        elif long_cond_str == "RSI_OVERSOLD" and "rsi" in ind_data:
            buy_mask = ind_data["rsi"] < ind_data["rsi_oversold"]
        elif long_cond_str == "BB_LOWER_BOUNCE" and "bb_lower" in ind_data:
            buy_mask = close < ind_data["bb_lower"]
        elif long_cond_str == "MACD_BULL_CROSS" and "macd_dif" in ind_data:
            buy_mask = (ind_data["macd_dif"] > ind_data["macd_dea"]) & (ind_data["macd_hist"] > 0)
        elif long_cond_str == "COMPOSITE_EMA_RSI" and "ema_fast" in ind_data and "rsi" in ind_data:
            buy_mask = (ind_data["ema_fast"] > ind_data["ema_slow"]) & (ind_data["rsi"] < ind_data["rsi_overbought"])

        # 解析空头条件
        if short_cond_str == "EMA_DEATH_CROSS" and "ema_fast" in ind_data:
            sell_mask = (ind_data["ema_fast"] < ind_data["ema_slow"]) & (ind_data["ema_fast"].shift(1) >= ind_data["ema_slow"].shift(1))
        elif short_cond_str == "RSI_OVERBOUGHT" and "rsi" in ind_data:
            sell_mask = ind_data["rsi"] > ind_data["rsi_overbought"]
        elif short_cond_str == "BB_UPPER_BREAK" and "bb_upper" in ind_data:
            sell_mask = close > ind_data["bb_upper"]
        elif short_cond_str == "MACD_BEAR_CROSS" and "macd_dif" in ind_data:
            sell_mask = (ind_data["macd_dif"] < ind_data["macd_dea"]) & (ind_data["macd_hist"] < 0)
        elif short_cond_str == "COMPOSITE_EMA_RSI" and "ema_fast" in ind_data and "rsi" in ind_data:
            sell_mask = (ind_data["ema_fast"] < ind_data["ema_slow"]) | (ind_data["rsi"] > ind_data["rsi_overbought"])

        signals[buy_mask] = 1
        signals[sell_mask] = -1

        # 持仓延续 (如果产生开仓信号，保持持仓直到出现反向信号)
        sig_arr = signals.to_numpy(copy=True)
        cur_pos = 0
        for i in range(len(sig_arr)):
            if sig_arr[i] != 0:
                cur_pos = sig_arr[i]
            sig_arr[i] = cur_pos

        return pd.Series(sig_arr, index=df.index)

# ================= 策略工厂与注册中心 =================
class StrategyRegistry:
    """全量量化策略注册中心"""
    _strategies: Dict[str, Any] = {
        "laya_momentum": LayaMomentumStrategy,
        "dual_ema": DualEMAStrategy,
        "macd_cross": MACDCrossStrategy,
        "supertrend": SuperTrendStrategy,
        "donchian_breakout": DonchianBreakoutStrategy,
        "bollinger": BollingerBandsStrategy,
        "rsi_mean_reversion": RSIMeanReversionStrategy,
        "keltner_channel": KeltnerChannelStrategy,
        "stoch_rsi": StochRSIStrategy,
        "volatility_squeeze": VolatilitySqueezeStrategy,
        "dual_thrust": DualThrustStrategy,
        "mfi_divergence": MFIDivergenceStrategy,
        "custom_strategy": CustomRuleStrategy
    }

    @classmethod
    def get_strategy(cls, name: str, params: Dict[str, Any] = None) -> BaseStrategy:
        strat_key = name.lower().strip()
        strat_cls = cls._strategies.get(strat_key, LayaMomentumStrategy)
        return strat_cls(params or {})

    @classmethod
    def list_strategies(cls) -> List[Dict[str, Any]]:
        """获取所有可用策略的简要清单"""
        result = []
        for key, strat_cls in cls._strategies.items():
            cat_meta = STRATEGY_CATALOG.get(key, {})
            result.append({
                "id": key,
                "name": strat_cls.name,
                "description": strat_cls.description,
                "category": getattr(strat_cls, "category", "经典策略"),
                "badge": cat_meta.get("badge", "标准策略"),
                "tag_color": cat_meta.get("tag_color", "blue")
            })
        return result

    @classmethod
    def get_catalog_details(cls) -> Dict[str, Any]:
        """获取带数学公式与教学内容的完整策略档案"""
        return STRATEGY_CATALOG
