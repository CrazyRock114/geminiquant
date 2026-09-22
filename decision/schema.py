"""
OmniQuant Decision Schema Specifications for Laya / Jev Non-Autoregressive Gating
"""
from typing import Dict, List, Any
from pydantic import BaseModel

# Laya / Jev 决策标准问题定义
DECISION_CRITERIA: Dict[str, List[Any]] = {
    # 核心动作判定
    "action": ["STRONG_BUY", "BUY", "HOLD", "REDUCE", "STRONG_SELL"],
    # 执行紧迫性
    "urgency": ["PASSIVE_MAKER", "AGGRESSIVE_TAKER", "CANCEL_ALL"],
    # 信号置信度
    "confidence": ["HIGH", "MEDIUM", "LOW"],
    # 前置一票否决风控
    "risk_passed": [True, False],
    # 仓位调仓幅度建议
    "size_factor": ["FULL", "HALF", "QUARTER", "ZERO"]
}

class DecisionResult(BaseModel):
    action: str
    urgency: str
    confidence: str
    risk_passed: bool
    size_factor: str
    action_probability: float = 1.0
    latency_ms: float = 0.0
    engine: str = "laya"
