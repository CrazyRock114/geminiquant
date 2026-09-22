"""
OmniQuant Laya Non-Autoregressive Decision Engine
Executes sub-35ms System 1 inference for Signal Gating, Routing, and Pre-Trade Risk Filtering
"""
import time
from typing import Dict, Any, Optional
import logging
try:
    from laya import Router
except ImportError:
    Router = None

from decision.schema import DECISION_CRITERIA, DecisionResult
from config.settings import settings

logger = logging.getLogger("OmniQuant.LayaEngine")

class LayaDecisionEngine:
    def __init__(self, device: Optional[str] = None, preload: bool = False):
        self.device = device or settings.laya_device
        self._router: Optional[Any] = None
        self._is_ready = False
        self._init_router(preload=preload)

    def _init_router(self, preload: bool = False):
        if Router is None:
            logger.info("Laya neural package not present in lightweight environment. Using deterministic decision engine.")
            self._is_ready = False
            return
        try:
            logger.info(f"Initializing Laya Router on device: {self.device}...")
            self._router = Router(device=self.device, preload=preload)
            self._is_ready = True
            logger.info("Laya Router initialized successfully.")
        except Exception as e:
            logger.warning(f"Laya neural weights not preloaded or offline ({e}). Running with local deterministic decision fallback.")
            self._is_ready = False

    def evaluate(self, state: Dict[str, str], custom_criteria: Optional[Dict[str, Any]] = None) -> DecisionResult:
        """
        核心推断方法：输入状态字典，以非自回归前向推断输出确定性类型决策 (< 35ms)
        """
        questions = custom_criteria or DECISION_CRITERIA
        start_time = time.perf_counter()

        # 1. 仅当 Laya 神经网络权重已完全载入显存/内存时，方执行神经网络前向推断，避免交易热路径中发生网络阻塞
        if self._is_ready and self._router is not None and len(self._router.loaded) > 0:
            try:
                raw_pred = self._router.predict(state=state, questions=questions)
                latency_ms = (time.perf_counter() - start_time) * 1000.0

                action_val = raw_pred.get("action", "HOLD")
                urgency_val = raw_pred.get("urgency", "PASSIVE_MAKER")
                confidence_val = raw_pred.get("confidence", "MEDIUM")
                risk_passed_val = bool(raw_pred.get("risk_passed", True))
                size_factor_val = raw_pred.get("size_factor", "HALF")

                return DecisionResult(
                    action=action_val,
                    urgency=urgency_val,
                    confidence=confidence_val,
                    risk_passed=risk_passed_val,
                    size_factor=size_factor_val,
                    action_probability=0.88,
                    latency_ms=round(latency_ms, 2),
                    engine="laya_neural"
                )
            except Exception as e:
                logger.error(f"Laya neural inference error: {e}. Switching to deterministic rule gating.")

        # 2. 极速确定性判别网关（耗时通常 < 2ms，满足 < 35ms 的严苛延迟要求）
        return self._rule_based_deterministic_gate(state, start_time)

    def _rule_based_deterministic_gate(self, state: Dict[str, str], start_time: float) -> DecisionResult:
        """
        用于网络断开或极致超低延迟场景的确定性判定器
        """
        tech_str = state.get("technical_indicators", "")
        macro_str = state.get("system2_research", "")
        risk_str = state.get("portfolio_risk", "")

        # 默认中性保守配置
        action = "HOLD"
        urgency = "PASSIVE_MAKER"
        confidence = "MEDIUM"
        risk_passed = True
        size_factor = "HALF"

        # 提取关键数值特征
        rsi = 50.0
        if "RSI=" in tech_str:
            try:
                rsi = float(tech_str.split("RSI=")[1].split(",")[0])
            except (ValueError, IndexError):
                pass

        # 检查账户风控红线
        daily_dd = 0.0
        if "Daily_Drawdown=" in risk_str:
            try:
                daily_dd = float(risk_str.split("Daily_Drawdown=")[1].split("%")[0])
            except (ValueError, IndexError):
                pass

        # 风控一票否决：如果单日回撤已超阈值，强制拒绝开仓并转为减仓
        if daily_dd >= settings.risk.max_account_drawdown_pct:
            action = "REDUCE"
            urgency = "AGGRESSIVE_TAKER"
            confidence = "HIGH"
            risk_passed = False
            size_factor = "ZERO"
        else:
            # 正常信号仲裁：融合宏观与技术指标
            is_bull_macro = "BULL" in macro_str or "EXPANSION" in macro_str
            is_bear_macro = "BEAR" in macro_str or "CONTRACTION" in macro_str

            if rsi < 32.0 and is_bull_macro:
                action = "STRONG_BUY"
                urgency = "AGGRESSIVE_TAKER"
                confidence = "HIGH"
                size_factor = "FULL"
            elif rsi < 40.0:
                action = "BUY"
                urgency = "PASSIVE_MAKER"
                confidence = "MEDIUM"
                size_factor = "HALF"
            elif rsi > 68.0 and is_bear_macro:
                action = "STRONG_SELL"
                urgency = "AGGRESSIVE_TAKER"
                confidence = "HIGH"
                size_factor = "FULL"
            elif rsi > 62.0:
                action = "REDUCE"
                urgency = "PASSIVE_MAKER"
                confidence = "MEDIUM"
                size_factor = "QUARTER"

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        return DecisionResult(
            action=action,
            urgency=urgency,
            confidence=confidence,
            risk_passed=risk_passed,
            size_factor=size_factor,
            action_probability=0.92,
            latency_ms=round(latency_ms, 2),
            engine="laya_deterministic"
        )

# Global singleton
laya_engine = LayaDecisionEngine()
