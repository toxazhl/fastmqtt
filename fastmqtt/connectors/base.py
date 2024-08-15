import asyncio
import uuid
from abc import ABC, abstractmethod
from typing import Awaitable, Callable

from fastmqtt.properties import (
    ConnectProperties,
    PublishProperties,
    SubscribeProperties,
    UnsubscribeProperties,
)
from fastmqtt.types import CleanStart, PayloadType, RawMessage, SubscribeOptions


class BaseConnector(ABC):
    def __init__(
        self,
        hostname: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        client_id: str | None = None,
        will=None,
        keepalive: int = 60,
        properties: ConnectProperties | None = None,
        clean_start: CleanStart = CleanStart.FIRST_ONLY,
    ):
        if client_id is None:
            client_id = f"fastmqtt-{uuid.uuid4()}"

        self._hostname = hostname
        self._port = port
        self._username = username
        self._password = password
        self._client_id = client_id
        self._will = will
        self._keepalive = keepalive
        self._properties = properties
        self._clean_start = clean_start

        self.connected_event = asyncio.Event()
        self.disconnected_event = asyncio.Event()
        self.reconnect_event = asyncio.Event()

        self._first_connect = True

        self._connect_callbacks: list[Callable[[], Awaitable[None]]] = []
        self._disconnect_callbacks: list[Callable[[], Awaitable[None]]] = []
        self._message_callbacks: list[Callable[[RawMessage], Awaitable[None]]] = []

    @property
    def identifier(self) -> str:
        return self._client_id

    @abstractmethod
    async def subscribe(
        self,
        topic: str,
        options: SubscribeOptions | None = None,
        properties: SubscribeProperties | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def subscribe_multiple(
        self,
        topics: list[tuple[str, SubscribeOptions]],
        properties: SubscribeProperties | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe(
        self, topic: str, properties: UnsubscribeProperties | None = None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe_multiple(
        self, topics: list[str], properties: UnsubscribeProperties | None = None
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def publish(
        self,
        topic: str,
        payload: PayloadType = None,
        qos: int = 0,
        retain: bool = False,
        properties: PublishProperties | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    def add_connect_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._connect_callbacks.append(callback)

    def add_disconnect_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._disconnect_callbacks.append(callback)

    def add_message_callback(self, callback: Callable[[RawMessage], Awaitable[None]]) -> None:
        self._message_callbacks.append(callback)
