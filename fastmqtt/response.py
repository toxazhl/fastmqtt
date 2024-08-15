import asyncio
import itertools
import logging
from typing import TYPE_CHECKING, Any, Callable

from .exceptions import FastMQTTError
from .properties import PublishProperties
from .subscription_manager import SubscriptionWithId
from .types import Message, RetainHandling

if TYPE_CHECKING:
    from .fastmqtt import FastMQTT

log = logging.getLogger(__name__)


class CorrelationIntGenerator:
    def __init__(self, limit: int = 2**16):
        self._correlation_data_counter = itertools.cycle(range(1, limit))

    def __call__(self) -> bytes:
        val = next(self._correlation_data_counter)
        return val.to_bytes((val.bit_length() + 7) // 8, "big")


class ResponseContext:
    def __init__(
        self,
        fastmqtt: "FastMQTT",
        response_topic: str,
        qos: int = 0,
        default_timeout: float | None = 60,
        correlation_generator: Callable[[], bytes] = CorrelationIntGenerator(),
        payload_encoder: Callable[[Any], bytes] = lambda x: x,
    ):
        self._fastmqtt = fastmqtt
        self._response_topic = response_topic
        self._qos = qos
        self._default_timeout = default_timeout
        self._futures: dict[bytes, asyncio.Future[Message]] = {}
        self._subscription: SubscriptionWithId | None = None
        self._correlation_generator = correlation_generator

    async def subscribe(self) -> None:
        self._subscription = await self._fastmqtt.subscribe(
            callback=self._callback,
            topic=self._response_topic,
            qos=self._qos,
            retain_handling=RetainHandling.DO_NOT_SEND,
        )

    async def close(self) -> None:
        if self._subscription is not None:
            await self._fastmqtt.unsubscribe(subscription=self._subscription)

        self._subscription = None

        for future in self._futures.values():
            future.cancel()

    async def __aenter__(self):
        await self.subscribe()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def _callback(self, message: Message) -> None:
        correlation_data = message.properties.correlation_data
        if correlation_data is None:
            log.error(f"correlation_data is None in response callback ({message.topic})")
            return

        future = self._futures.pop(correlation_data, None)
        if future is None:
            log.error(f"correlation_data {correlation_data} not found in futures")
            return

        future.set_result(message)

    async def request(
        self,
        topic: str,
        payload: Any = None,
        qos: int = 0,
        retain: bool = False,
        properties: PublishProperties | None = None,
        timeout: float | None = None,
    ) -> Message:
        correlation_data = self._correlation_generator()
        if correlation_data in self._futures:
            raise FastMQTTError(f"correlation_data {correlation_data} already in use")

        if properties is None:
            properties = PublishProperties()

        if properties.correlation_data is not None:
            raise FastMQTTError("properties.correlation_data is not allowed in request")

        if properties.response_topic is not None:
            raise FastMQTTError("properties.response_topic is not allowed in request")

        properties.correlation_data = correlation_data
        properties.response_topic = self._response_topic

        future = asyncio.Future[Message]()
        self._futures[correlation_data] = future
        try:
            async with asyncio.timeout(timeout or self._default_timeout):
                await self._fastmqtt.publish(
                    topic=topic,
                    payload=payload,
                    qos=qos,
                    retain=retain,
                    properties=properties,
                )
                return await future

        finally:
            self._futures.pop(correlation_data, None)
