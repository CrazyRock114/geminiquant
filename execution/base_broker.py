"""
OmniQuant Abstract Broker Gateway Interface (QIFI Standard)
"""
from abc import ABC, abstractmethod
from typing import Dict
from core.models.order import OrderRequest, OrderReport, Position, AccountBalance

class BaseBroker(ABC):
    @abstractmethod
    async def connect(self) -> bool:
        """建立经纪商/柜台连接"""
        pass

    @abstractmethod
    async def disconnect(self):
        """断开连接"""
        pass

    @abstractmethod
    async def send_order(self, order: OrderRequest) -> OrderReport:
        """发送报单委托"""
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str) -> bool:
        """撤销订单"""
        pass

    @abstractmethod
    async def query_positions(self) -> Dict[str, Position]:
        """查询持仓明细"""
        pass

    @abstractmethod
    async def query_account(self) -> AccountBalance:
        """查询账户权益"""
        pass
