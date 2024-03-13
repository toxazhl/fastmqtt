from typing import Any

from paho.mqtt.properties import Properties


def properties_from_dict(properties: dict[str, Any], packet_type: int) -> Properties:
    mqtt_properties = Properties(packet_type)
    for key, value in properties.items():
        setattr(mqtt_properties, key, value)

    return mqtt_properties
