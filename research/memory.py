"""
OmniQuant System 2 Research Memory & Regime Cache
Maintains persistent macro states, sentiment indexes, and Bull/Bear debate summaries.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import json
from pathlib import Path
from config.settings import settings

class ResearchMemory:
    def __init__(self, memory_path: Optional[Path] = None):
        self.memory_path = memory_path or (settings.project_root / "config" / "macro_regime.json")
        self.current_state: Dict[str, Any] = {
            "regime": "BULL_EXPANSION",
            "debate_winner": "BULL",
            "sentiment": 0.65,
            "catalyst": "Rate cut cycle expectation & commodity reflation",
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.load()

    def load(self):
        if self.memory_path.exists():
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    self.current_state = json.load(f)
            except Exception:
                pass

    def save(self):
        try:
            self.memory_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump(self.current_state, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def update_regime(self, regime: str, debate_winner: str, sentiment: float, catalyst: str):
        self.current_state = {
            "regime": regime,
            "debate_winner": debate_winner,
            "sentiment": sentiment,
            "catalyst": catalyst,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
        self.save()

    def get_latest_context(self) -> Dict[str, Any]:
        return self.current_state

# Global singleton
research_memory = ResearchMemory()
