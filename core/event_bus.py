"""
OmniQuant High-Performance Asynchronous Event Bus
"""
import asyncio
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger("OmniQuant.EventBus")

class EventType:
    TICK = "TICK"
    BAR = "BAR"
    ORDER_BOOK = "ORDER_BOOK"
    SYSTEM2_RESEARCH = "SYSTEM2_RESEARCH"
    LAYA_DECISION = "LAYA_DECISION"
    RISK_INTERCEPT = "RISK_INTERCEPT"
    ORDER_SUBMIT = "ORDER_SUBMIT"
    ORDER_REPORT = "ORDER_REPORT"
    ACCOUNT_UPDATE = "ACCOUNT_UPDATE"

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._running: bool = False
        self._queue: asyncio.Queue = asyncio.Queue()

    def subscribe(self, event_type: str, handler: Callable):
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        if handler not in self._handlers[event_type]:
            self._handlers[event_type].append(handler)
            logger.debug(f"Subscribed {handler.__name__} to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable):
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)

    async def publish(self, event_type: str, data: Any):
        """异步入队发布"""
        await self._queue.put((event_type, data))

    def publish_sync(self, event_type: str, data: Any):
        """同步直接分发（用于亚毫秒级风控紧急熔断）"""
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    asyncio.create_task(handler(data))
                else:
                    handler(data)
            except Exception as e:
                logger.error(f"Error handling sync event {event_type} in {handler}: {e}", exc_info=True)

    async def start(self):
        self._running = True
        logger.info("EventBus started processing queue.")
        while self._running:
            try:
                event_type, data = await self._queue.get()
                handlers = self._handlers.get(event_type, [])
                for handler in handlers:
                    try:
                        if asyncio.iscoroutinefunction(handler):
                            await handler(data)
                        else:
                            handler(data)
                    except Exception as e:
                        logger.error(f"Error handling event {event_type} in {handler}: {e}", exc_info=True)
                self._queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"EventBus dispatch error: {e}", exc_info=True)

    def stop(self):
        self._running = False

# Global EventBus instance
event_bus = EventBus()
