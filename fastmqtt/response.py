import asyncio
import itertools
from typing import TYPE_CHECKING, Any, Callable

from aiomqtt.types import PayloadType

from .exceptions import FastMQTTError
from .structures import Message
from .subscription_manager import Retain, Subscription

if TYPE_CHECKING:
    from .fastmqtt import FastMQTT


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
    ):
        self._fastmqtt = fastmqtt
        self._response_topic = response_topic
        self._qos = qos
        self._default_timeout = default_timeout
        self._futures: dict[bytes, asyncio.Future[Message]] = {}
        self._subscription: Subscription | None = None
        self._identifier: int | None = None
        self._correlation_generator = correlation_generator

    async def subscribe(self) -> None:
        self._subscription = self._fastmqtt.register(
            self._callback,
            self._response_topic,
            self._qos,
            retain_handling=Retain.DO_NOT_SEND,
        )
        self._identifier = await self._fastmqtt._sub_manager.subscribe(self._subscription)

    async def close(self) -> None:
        if self._identifier is not None:
            await self._fastmqtt._sub_manager.unsubscribe(self._identifier, self._callback)

        self._identifier = None
        self._subscription = None
        for future in self._futures.values():
            future.cancel()

    async def __aenter__(self):
        await self.subscribe()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.close()

    async def _callback(self, message: Message) -> None:
        correlation_data = message.properties.get("CorrelationData")
        if correlation_data is None:
            raise FastMQTTError(f"correlation_data is None in response callback ({message.topic})")

        future = self._futures.pop(correlation_data)
        future.set_result(message)

    async def request(
        self,
        topic: str,
        payload: PayloadType = None,
        qos: int = 0,
        retain: bool = False,
        properties: dict[str, Any] | None = None,
        timeout: float | None = None,
    ) -> Message:
        if properties is None:
            properties = {}

        correlation_data = self._correlation_generator()

        properties["CorrelationData"] = correlation_data
        properties["ResponseTopic"] = self._response_topic

        if correlation_data in self._futures:
            raise FastMQTTError(f"correlation_data {correlation_data} already in use")

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
