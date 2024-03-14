import json
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import aiomqtt

from .utils import properties_to_dict

if TYPE_CHECKING:
    from .fastmqtt import FastMQTT


class Payload:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def raw(self) -> bytes:
        return self._data

    def text(self) -> str:
        return self._data.decode("utf-8")

    def json(self, **kwargs) -> dict[str, Any]:
        return json.loads(self._data, **kwargs)


@dataclass(frozen=True)
class Message:
    fastmqtt: "FastMQTT"

    topic: str
    payload: Payload
    qos: int
    retain: bool
    mid: int
    properties: dict[str, Any]

    @classmethod
    def _from_aiomqtt_message(cls, fastmqtt: "FastMQTT", message: aiomqtt.Message) -> "Message":
        return cls(
            fastmqtt=fastmqtt,
            topic=str(message.topic),
            payload=Payload(message.payload),  # type: ignore
            qos=message.qos,
            retain=message.retain,
            mid=message.mid,
            properties=properties_to_dict(message.properties)
            if message.properties is not None
            else {},
        )
