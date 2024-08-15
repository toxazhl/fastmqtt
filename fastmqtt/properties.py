import enum
from dataclasses import dataclass, field


class PacketTypes(enum.IntEnum):
    CONNECT = 1
    CONNACK = 2
    PUBLISH = 3
    PUBACK = 4
    PUBREC = 5
    PUBREL = 6
    PUBCOMP = 7
    SUBSCRIBE = 8
    SUBACK = 9
    UNSUBSCRIBE = 10
    UNSUBACK = 11
    PINGREQ = 12
    PINGRESP = 13
    DISCONNECT = 14
    AUTH = 15
    WILLMESSAGE = 16  # This is not a real MQTT packet type, but used in the original code


@dataclass
class BaseProperties:
    user_property: list[tuple[str, str]] = field(default_factory=list)


@dataclass
class ConnectProperties(BaseProperties):
    session_expiry_interval: int | None = None
    authentication_method: str | None = None
    authentication_data: bytes | None = None
    request_problem_information: int | None = None
    request_response_information: int | None = None
    receive_maximum: int | None = None
    topic_alias_maximum: int | None = None
    maximum_packet_size: int | None = None


@dataclass
class ConnackProperties(BaseProperties):
    session_expiry_interval: int | None = None
    assigned_client_identifier: str | None = None
    server_keep_alive: int | None = None
    authentication_method: str | None = None
    authentication_data: bytes | None = None
    response_information: str | None = None
    server_reference: str | None = None
    reason_string: str | None = None
    receive_maximum: int | None = None
    topic_alias_maximum: int | None = None
    maximum_qos: int | None = None
    retain_available: int | None = None
    maximum_packet_size: int | None = None
    wildcard_subscription_available: int | None = None
    subscription_identifier_available: int | None = None
    shared_subscription_available: int | None = None


@dataclass
class PublishProperties(BaseProperties):
    payload_format_indicator: int | None = None
    message_expiry_interval: int | None = None
    content_type: str | None = None
    response_topic: str | None = None
    correlation_data: bytes | None = None
    subscription_identifier: bytes | None = None
    topic_alias: int | None = None


@dataclass
class PubackProperties(BaseProperties):
    reason_string: str | None = None


@dataclass
class PubrecProperties(BaseProperties):
    reason_string: str | None = None


@dataclass
class PubrelProperties(BaseProperties):
    reason_string: str | None = None


@dataclass
class PubcompProperties(BaseProperties):
    reason_string: str | None = None


@dataclass
class SubscribeProperties(BaseProperties):
    subscription_identifier: int | None = None


@dataclass
class SubackProperties(BaseProperties):
    reason_string: str | None = None


@dataclass
class UnsubscribeProperties(BaseProperties):
    pass


@dataclass
class UnsubackProperties(BaseProperties):
    reason_string: str | None = None


@dataclass
class DisconnectProperties(BaseProperties):
    session_expiry_interval: int | None = None
    server_reference: str | None = None
    reason_string: str | None = None


@dataclass
class AuthProperties(BaseProperties):
    authentication_method: str | None = None
    authentication_data: bytes | None = None
    reason_string: str | None = None


@dataclass
class WillMessageProperties(BaseProperties):
    payload_format_indicator: int | None = None
    message_expiry_interval: int | None = None
    content_type: str | None = None
    response_topic: str | None = None
    correlation_data: bytes | None = None
    will_delay_interval: int | None = None
