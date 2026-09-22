"""
OmniQuant Unified Feature & Quantitative Indicator Engine
Computes Technical Indicators, Orderbook Microstructure (OFI), and Options Greeks (Black-Scholes)
"""
import math
import pandas as pd
from scipy.stats import norm
from typing import Dict
from core.models.types import OptionType

class FeatureEngine:
    @staticmethod
    def calculate_rsi(series: pd.Series, period: int = 14) -> float:
        """相对强弱指标 RSI"""
        if len(series) < period + 1:
            return 50.0
        delta = series.diff()
        gain = delta.where(delta > 0, 0.0)
        loss = -delta.where(delta < 0, 0.0)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()
        rs = avg_gain / (avg_loss + 1e-10)
        rsi = 100.0 - (100.0 / (1.0 + rs))
        return float(rsi.iloc[-1])

    @staticmethod
    def calculate_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, float]:
        """指数平滑异同移动平均线 MACD"""
        if len(series) < slow + signal:
            return {"macd": 0.0, "signal": 0.0, "hist": 0.0}
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        sig = macd.ewm(span=signal, adjust=False).mean()
        hist = macd - sig
        return {
            "macd": float(macd.iloc[-1]),
            "signal": float(sig.iloc[-1]),
            "hist": float(hist.iloc[-1])
        }

    @staticmethod
    def calculate_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Dict[str, float]:
        """布林带 (Bollinger Bands) 与带宽"""
        if len(series) < window:
            val = float(series.iloc[-1]) if len(series) > 0 else 0.0
            return {"upper": val, "middle": val, "lower": val, "bandwidth": 0.0}
        rolling_mean = series.rolling(window=window).mean()
        rolling_std = series.rolling(window=window).std()
        upper = rolling_mean + (rolling_std * num_std)
        lower = rolling_mean - (rolling_std * num_std)
        mid = rolling_mean.iloc[-1]
        bw = (upper.iloc[-1] - lower.iloc[-1]) / (mid + 1e-10)
        return {
            "upper": float(upper.iloc[-1]),
            "middle": float(mid),
            "lower": float(lower.iloc[-1]),
            "bandwidth": float(bw)
        }

    @staticmethod
    def calculate_black_scholes_greeks(
        S: float,          # 标的资产当前价格
        K: float,          # 期权行权价
        T: float,          # 到期剩余时间（年化，如30天为 30/365）
        r: float = 0.025,  # 无风险利率
        sigma: float = 0.20, # 波动率 (IV)
        option_type: OptionType = OptionType.CALL
    ) -> Dict[str, float]:
        """
        基于 Black-Scholes 解析模型计算期权理论价格与核心 Greeks
        Delta, Gamma, Vega, Theta
        """
        if T <= 0 or sigma <= 0 or S <= 0 or K <= 0:
            return {"price": 0.0, "delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0}

        d1 = (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
        d2 = d1 - sigma * math.sqrt(T)

        if option_type == OptionType.CALL:
            price = S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2)
            delta = norm.cdf(d1)
            theta = (- (S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
                     - r * K * math.exp(-r * T) * norm.cdf(d2)) / 365.0
        else:
            price = K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
            delta = norm.cdf(d1) - 1.0
            theta = (- (S * norm.pdf(d1) * sigma) / (2 * math.sqrt(T))
                     + r * K * math.exp(-r * T) * norm.cdf(-d2)) / 365.0

        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
        vega = (S * norm.pdf(d1) * math.sqrt(T)) / 100.0  # 每 1% 波动率变动带来的期权价格变化

        return {
            "price": round(float(price), 4),
            "delta": round(float(delta), 4),
            "gamma": round(float(gamma), 4),
            "vega": round(float(vega), 4),
            "theta": round(float(theta), 4)
        }

# Global singleton
feature_engine = FeatureEngine()
