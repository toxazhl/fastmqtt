from typing import Any

from paho.mqtt.properties import Properties


def properties_from_dict(properties: dict[str, Any], packet_type: int) -> Properties:
    mqtt_properties = Properties(packet_type)
    for key, value in properties.items():
        setattr(mqtt_properties, key, value)

    return mqtt_properties


def properties_to_dict(properties: Properties) -> dict[str, Any]:
    data = {}
    for name in properties.names:
        compressed_name = name.replace(" ", "")
        if hasattr(properties, compressed_name):
            val = getattr(properties, compressed_name)
            data[compressed_name] = val
    return data
