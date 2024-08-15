import aiomqtt

from fastmqtt.properties import PublishProperties
from fastmqtt.types import Payload, Message

from .properties import paho_to_fastmqtt_properties


def aiomqtt_to_fastmqtt_message(message: aiomqtt.Message) -> Message:
    properties = PublishProperties()
    if message.properties is not None:
        properties = paho_to_fastmqtt_properties(message.properties)

    if not isinstance(properties, PublishProperties):
        raise ValueError("Properties must be PublishProperties")

    return Message(
        topic=str(message.topic),
        payload=Payload(message.payload),  # type: ignore
        qos=message.qos,
        retain=message.retain,
        mid=message.mid,
        properties=properties,
    )
