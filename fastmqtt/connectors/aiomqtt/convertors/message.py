import aiomqtt

from fastmqtt.properties import PublishProperties
from fastmqtt.types import RawMessage

from .properties import paho_to_fastmqtt_properties


def aiomqtt_to_fastmqtt_message(message: aiomqtt.Message) -> RawMessage:
    properties = PublishProperties()
    if message.properties is not None:
        properties = paho_to_fastmqtt_properties(message.properties)

    if not isinstance(properties, PublishProperties):
        raise ValueError("Properties must be PublishProperties")

    return RawMessage(
        topic=str(message.topic),
        payload=message.payload,  # type: ignore
        qos=message.qos,
        retain=message.retain,
        mid=message.mid,
        properties=properties,
    )
