"""
OmniQuant Global Settings & Configuration Center
"""
import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class MarketTimezones(BaseModel):
    CHINA: str = "Asia/Shanghai"
    US: str = "America/New_York"
    CRYPTO: str = "UTC"
    LONDON: str = "Europe/London"

class RiskLimits(BaseModel):
    max_account_drawdown_pct: float = Field(default=3.0, description="Max daily drawdown before hard kill-switch")
    max_position_ratio_pct: float = Field(default=20.0, description="Max single position value as % of equity")
    max_leverage: float = Field(default=3.0, description="Max overall leverage factor")
    max_option_delta_exposure: float = Field(default=0.30, description="Max absolute portfolio delta")
    max_slippage_bps: float = Field(default=30.0, description="Max allowable execution slippage in bps (0.3%)")

class Settings(BaseModel):
    project_root: Path = PROJECT_ROOT
    env: str = os.getenv("OMNIQUANT_ENV", "paper")
    debug: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    # Timezones
    timezones: MarketTimezones = MarketTimezones()

    # Risk settings
    risk: RiskLimits = RiskLimits()

    # System 1 Decision Engine
    decision_engine: str = os.getenv("DECISION_ENGINE", "laya") # 'laya', 'jev', 'rule_fallback'
    laya_device: str = os.getenv("LAYA_DEVICE", "mps") # 'mps', 'cpu', 'cuda'
    jev_api_key: Optional[str] = os.getenv("JEV_API_KEY", None)

    # System 2 Research Engine (LLM)
    llm_provider: str = os.getenv("LLM_PROVIDER", "deepseek")
    llm_api_key: Optional[str] = os.getenv("LLM_API_KEY", None)
    llm_base_url: str = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    llm_model: str = os.getenv("LLM_MODEL", "deepseek-chat")

    # Data credentials
    openbb_pat: Optional[str] = os.getenv("OPENBB_PAT", None)
    polygon_api_key: Optional[str] = os.getenv("POLYGON_API_KEY", None)

    # Brokers / Gateways
    crypto_exchange: str = os.getenv("CRYPTO_EXCHANGE", "binance")
    crypto_testnet: bool = os.getenv("CRYPTO_TESTNET", "True").lower() in ("true", "1", "yes")
    crypto_api_key: Optional[str] = os.getenv("CRYPTO_API_KEY", None)
    crypto_secret: Optional[str] = os.getenv("CRYPTO_SECRET", None)

    ctp_user_id: Optional[str] = os.getenv("CTP_USER_ID", None)
    ctp_password: Optional[str] = os.getenv("CTP_PASSWORD", None)
    ctp_broker_id: str = os.getenv("CTP_BROKER_ID", "9999")
    ctp_md_front: str = os.getenv("CTP_MD_FRONT", "tcp://180.168.146.187:10131")
    ctp_td_front: str = os.getenv("CTP_TD_FRONT", "tcp://180.168.146.187:10130")

    qmt_path: Optional[str] = os.getenv("QMT_PATH", None)

    ibkr_host: str = os.getenv("IBKR_HOST", "127.0.0.1")
    ibkr_port: int = int(os.getenv("IBKR_PORT", "7497"))
    ibkr_client_id: int = int(os.getenv("IBKR_CLIENT_ID", "1"))

# Global singleton
settings = Settings()
