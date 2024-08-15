import enum
import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from .properties import PublishProperties

if TYPE_CHECKING:
    from .fastmqtt import FastMqtt


PayloadType = str | bytes | bytearray | int | float | None


class Payload:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def raw(self) -> bytes:
        return self._data

    def text(self, encoding: str = "utf-8") -> str:
        return self._data.decode(encoding=encoding)

    def json(
        self,
        encoder: Callable[[str], Any] = json.loads,
        **kwargs,
    ) -> Any:
        return encoder(self.text(), **kwargs)


class RetainHandling(enum.IntEnum):
    SEND_ON_SUBSCRIBE = 0
    SEND_IF_NEW_SUB = 1
    DO_NOT_SEND = 2


@dataclass
class SubscribeOptions:
    qos: int = 0
    no_local: bool = False
    retain_as_published: bool = False
    retain_handling: RetainHandling = RetainHandling.SEND_ON_SUBSCRIBE


@dataclass(frozen=True)
class Message:
    topic: str
    payload: Payload
    qos: int
    retain: bool
    mid: int
    properties: PublishProperties


@dataclass(frozen=True)
class MessageWithClient(Message):
    client: "FastMqtt"


CallbackType = Callable[[MessageWithClient], Coroutine[None, None, Any]]


@dataclass
class Subscription:
    callbacks: list[CallbackType]
    topic: str
    options: SubscribeOptions


@dataclass
class SubscriptionWithId(Subscription):
    id: int


class CleanStart(enum.IntEnum):
    NO = 0
    ALWAYS = 1
    FIRST_ONLY = 2  # Clean start only on first connection, do not clean start on reconnect
