"""
OmniQuant Decision State Builder
Synthesizes Market Microstructure, Feature Indicators, System 2 Research, and Risk Status
into a compact representation for sub-35ms Laya/Jev forward inference.
"""
from typing import Dict, Any
from core.models.market_data import TickData
from core.models.order import AccountBalance

class StateBuilder:
    @staticmethod
    def build_state(
        tick: TickData,
        technical_features: Dict[str, Any],
        system2_research: Dict[str, Any],
        account: AccountBalance
    ) -> Dict[str, str]:
        """
        将复杂上下文压制为高信息密度的语义状态槽
        """
        # 1. 行情与微观结构
        price_summary = (
            f"Symbol: {tick.symbol}, Asset: {tick.asset_class.value}, Last: {tick.last_price}, "
            f"Spread_Bps: {round((tick.ask_price_1 - tick.bid_price_1) / tick.last_price * 10000, 1) if (tick.ask_price_1 and tick.bid_price_1) else 0}"
        )

        # 2. 技术指标与动量特征
        tech_summary = (
            f"RSI={technical_features.get('rsi', 50.0):.1f}, "
            f"MACD_Hist={technical_features.get('macd_hist', 0.0):.2f}, "
            f"BB_Bandwidth={technical_features.get('bb_bandwidth', 0.0):.3f}, "
            f"OFI_Imbalance={technical_features.get('ofi', 0.0):.2f}"
        )

        # 3. System 2 宏观研报与多空博弈共识
        macro_summary = (
            f"Macro_Regime={system2_research.get('regime', 'RANGE_BOUND')}, "
            f"Debate_Winner={system2_research.get('debate_winner', 'NEUTRAL')}, "
            f"Sentiment_Score={system2_research.get('sentiment', 0.0):.2f}, "
            f"Catalyst={system2_research.get('catalyst', 'NONE')}"
        )

        # 4. 实时账户与风控边界
        risk_summary = (
            f"Daily_Drawdown={account.daily_drawdown_pct:.2f}%, "
            f"Peak_Drawdown={account.current_drawdown_pct:.2f}%, "
            f"Margin_Ratio={account.margin_ratio * 100:.1f}%, "
            f"Available_Cash={account.available_cash:.0f}"
        )

        return {
            "market_snapshot": price_summary,
            "technical_indicators": tech_summary,
            "system2_research": macro_summary,
            "portfolio_risk": risk_summary
        }

# Global singleton
state_builder = StateBuilder()
