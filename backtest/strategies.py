"""
OmniQuant Crypto Strategy Library
Contains standard quantitative trading strategies for cryptocurrency backtesting:
- LayaMomentumStrategy: Laya multi-feature momentum & Wilder RMA RSI with risk rules
- DualEMAStrategy: Fast & Slow Exponential Moving Average trend following
- BollingerBandsStrategy: Mean-reverting statistical arbitrage
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
import numpy as np
from data.feature_engine import FeatureEngine

class BaseStrategy(ABC):
    name: str = "BaseStrategy"
    description: str = "Base Strategy Description"

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

class LayaMomentumStrategy(BaseStrategy):
    """
    Laya 毫秒动量与自适应风控策略:
    结合 Wilder RMA RSI-14、EMA 趋势过滤与微观反转动量。
    在牛市/扩张期顺势进攻，在超买或动能衰竭时快速防守撤离。
    """
    name = "Laya 极速动量风控策略"
    description = "集成 Wilder RMA RSI-14 与 EMA 双通道动量过滤，兼具自适应止盈防守机制"

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"]
        rsi_period = int(self.params.get("rsi_period", 14))
        oversold_threshold = float(self.params.get("oversold", 35.0))
        overbought_threshold = float(self.params.get("overbought", 68.0))

        # 计算 Wilder RSI 与双 EMA
        rsi = FeatureEngine.calculate_rsi(close, period=rsi_period)
        ema_fast = close.ewm(span=12, adjust=False).mean()
        ema_slow = close.ewm(span=26, adjust=False).mean()

        signals = pd.Series(0, index=df.index, dtype=int)

        # 规则逻辑:
        # 1. 超跌反弹或多头金叉加速: RSI < oversold 或 (EMA金叉 且 RSI 在中性上升区间)
        buy_cond = (rsi < oversold_threshold) | ((ema_fast > ema_slow) & (rsi >= 48) & (rsi <= overbought_threshold))
        
        # 2. 超买钝化或空头死叉破位: RSI > overbought 或 (EMA死叉 且 RSI < 45)
        sell_cond = (rsi > overbought_threshold) | ((ema_fast < ema_slow) & (rsi < 45))

        signals[buy_cond] = 1
        signals[sell_cond] = -1

        return signals

class DualEMAStrategy(BaseStrategy):
    """双均线趋势跟踪策略 (EMA-12 / EMA-26)"""
    name = "双均线趋势跟踪策略"
    description = "经典快速与慢速指数移动平均线交叉趋势跟踪系统"

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

class BollingerBandsStrategy(BaseStrategy):
    """布林带均值回归策略 (Bollinger Bands 20, 2)"""
    name = "布林带均值回归策略"
    description = "基于统计学 2 倍标准差上下轨道的统计套利与震荡反转策略"

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

class StrategyRegistry:
    """策略工厂与注册中心"""
    _strategies = {
        "laya_momentum": LayaMomentumStrategy,
        "dual_ema": DualEMAStrategy,
        "bollinger": BollingerBandsStrategy,
    }

    @classmethod
    def get_strategy(cls, name: str, params: Dict[str, Any] = None) -> BaseStrategy:
        strat_cls = cls._strategies.get(name.lower(), LayaMomentumStrategy)
        return strat_cls(params or {})

    @classmethod
    def list_strategies(cls) -> List[Dict[str, str]]:
        return [
            {"id": key, "name": strat.name, "description": strat.description}
            for key, strat in cls._strategies.items()
        ]
