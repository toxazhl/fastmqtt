import enum
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Coroutine

from .properties import PublishProperties

if TYPE_CHECKING:
    from .encoders import BaseDecoder
    from .fastmqtt import FastMQTT


PayloadType = str | bytes | bytearray | int | float | None


class Payload:
    def __init__(self, data: bytes, decoder: "BaseDecoder") -> None:
        self._data = data
        self._decoder = decoder

    def raw(self) -> bytes:
        return self._data

    def decode(self) -> Any:
        return self._decoder(self._data)


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
class RawMessage:
    topic: str
    payload: bytes
    qos: int
    retain: bool
    mid: int
    properties: PublishProperties


@dataclass(frozen=True)
class Message(RawMessage):
    payload: Payload
    client: "FastMQTT"


CallbackType = Callable[[Message], Coroutine[None, None, Any]]


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
