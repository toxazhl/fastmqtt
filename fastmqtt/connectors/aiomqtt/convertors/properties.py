from dataclasses import asdict
from typing import Any

import paho.mqtt.properties

from fastmqtt.properties import (
    AuthProperties,
    BaseProperties,
    ConnackProperties,
    ConnectProperties,
    DisconnectProperties,
    PacketTypes,
    PubackProperties,
    PubcompProperties,
    PublishProperties,
    PubrecProperties,
    PubrelProperties,
    SubackProperties,
    SubscribeProperties,
    UnsubackProperties,
    UnsubscribeProperties,
    WillMessageProperties,
)

ALL_PROPERTIES = (
    (ConnectProperties, PacketTypes.CONNECT),
    (ConnackProperties, PacketTypes.CONNACK),
    (PublishProperties, PacketTypes.PUBLISH),
    (PubackProperties, PacketTypes.PUBACK),
    (PubrecProperties, PacketTypes.PUBREC),
    (PubrelProperties, PacketTypes.PUBREL),
    (PubcompProperties, PacketTypes.PUBCOMP),
    (SubscribeProperties, PacketTypes.SUBSCRIBE),
    (SubackProperties, PacketTypes.SUBACK),
    (UnsubscribeProperties, PacketTypes.UNSUBSCRIBE),
    (UnsubackProperties, PacketTypes.UNSUBACK),
    (DisconnectProperties, PacketTypes.DISCONNECT),
    (AuthProperties, PacketTypes.AUTH),
    (WillMessageProperties, PacketTypes.WILLMESSAGE),
)


FASTMQTT_TYPE_TO_PAHO_PACKET_TYPE_MAPPING: dict[type[BaseProperties], int] = dict(ALL_PROPERTIES)

PAHO_PACKET_TYPE_TO_FASTMQTT_TYPE_MAPPING: dict[int, type[BaseProperties]] = {
    packet_type: properties for properties, packet_type in ALL_PROPERTIES
}


def paho_to_fastmqtt_properties(
    paho_properties: paho.mqtt.properties.Properties,
) -> BaseProperties:
    if paho_properties.packetType not in PAHO_PACKET_TYPE_TO_FASTMQTT_TYPE_MAPPING:
        raise ValueError(f"Unknown packet type: {paho_properties.packetType}")

    fastmqtt_properties_type = PAHO_PACKET_TYPE_TO_FASTMQTT_TYPE_MAPPING[
        paho_properties.packetType
    ]

    dict_properties: dict[str, Any] = {}
    private_vars = ["packetType", "types", "names", "properties"]
    for attr, value in paho_properties.__dict__.items():
        if attr in private_vars:
            continue

        snake_case_attr = "".join(["_" + c.lower() if c.isupper() else c for c in attr]).lstrip(
            "_"
        )
        dict_properties[snake_case_attr] = value
    return fastmqtt_properties_type(**dict_properties)


def fastmqtt_to_paho_properties(
    fastmqtt_properties: BaseProperties,
) -> paho.mqtt.properties.Properties:
    if type(fastmqtt_properties) not in FASTMQTT_TYPE_TO_PAHO_PACKET_TYPE_MAPPING:
        raise ValueError(f"Unknown properties type: {type(fastmqtt_properties)}")

    packet_type = FASTMQTT_TYPE_TO_PAHO_PACKET_TYPE_MAPPING[type(fastmqtt_properties)]
    paho_properties = paho.mqtt.properties.Properties(packet_type)

    for attr, value in asdict(fastmqtt_properties).items():
        if value is not None:
            camel_case_attr = "".join(word.capitalize() for word in attr.split("_"))
            setattr(paho_properties, camel_case_attr, value)

    return paho_properties
