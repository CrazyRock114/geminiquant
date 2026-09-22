"""
OmniQuant Decision Engine Fallback & Jev Integration
Provides seamless switching between Laya, TypeSafe Jev API, and Rule-based gating.
"""
import os
import requests
import logging
from typing import Dict, Any, Optional
from decision.schema import DecisionResult, DECISION_CRITERIA
from decision.laya_engine import laya_engine
from config.settings import settings

logger = logging.getLogger("OmniQuant.DecisionFactory")

class JevDecisionEngine:
    """TypeSafe Jev 商业 API 客户端适配器"""
    def __init__(self, api_key: Optional[str] = None, endpoint: Optional[str] = None):
        self.api_key = api_key or settings.jev_api_key
        self.endpoint = endpoint or os.getenv("JEV_ENDPOINT", "https://api.typesafe.ai/v1/decision")

    def evaluate(self, state: Dict[str, str], questions: Optional[Dict[str, Any]] = None) -> DecisionResult:
        if not self.api_key:
            logger.warning("Jev API Key not configured. Falling back to Laya.")
            return laya_engine.evaluate(state, questions)

        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        payload = {"state": state, "questions": questions or DECISION_CRITERIA}
        try:
            resp = requests.post(self.endpoint, json=payload, headers=headers, timeout=2.0)
            resp.raise_for_status()
            data = resp.json()
            return DecisionResult(
                action=data.get("action", "HOLD"),
                urgency=data.get("urgency", "PASSIVE_MAKER"),
                confidence=data.get("confidence", "MEDIUM"),
                risk_passed=bool(data.get("risk_passed", True)),
                size_factor=data.get("size_factor", "HALF"),
                action_probability=data.get("probability", 0.90),
                latency_ms=data.get("latency_ms", 45.0),
                engine="jev_api"
            )
        except Exception as e:
            logger.error(f"Jev API request failed: {e}. Falling back to Laya engine.")
            return laya_engine.evaluate(state, questions)

def get_decision_engine():
    """获取当前配置的决策引擎实例 (Laya / Jev)"""
    engine_name = settings.decision_engine.lower()
    if engine_name == "jev":
        return JevDecisionEngine()
    return laya_engine
