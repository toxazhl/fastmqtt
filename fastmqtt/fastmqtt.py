import asyncio
import logging
import ssl
from typing import Any, Callable, Iterable, Sequence

import paho.mqtt.client as mqtt
from aiomqtt import Client as MQTTClient
from aiomqtt import (
    Message,
    ProtocolVersion,
    ProxySettings,
    TLSParameters,
    Will,
)
from aiomqtt.types import PayloadType, SocketOption
from paho.mqtt.packettypes import PacketTypes

from .message_handler import MessageHandler
from .response import ResponseContext
from .router import MQTTRouter
from .subscription_manager import Subscription, SubscriptionManager
from .utils import properties_from_dict

WebSocketHeaders = dict[str, str] | Callable[[dict[str, str]], dict[str, str]]


class FastMQTT(MQTTRouter):
    def __init__(
        self,
        hostname: str,
        port: int = 1883,
        *,
        username: str | None = None,
        password: str | None = None,
        logger: logging.Logger | None = None,
        identifier: str | None = None,
        queue_type: type[asyncio.Queue[Message]] | None = None,
        will: Will | None = None,
        clean_session: bool | None = None,
        transport: str = "tcp",
        timeout: float | None = None,
        keepalive: int = 60,
        bind_address: str = "",
        bind_port: int = 0,
        clean_start: int = mqtt.MQTT_CLEAN_START_FIRST_ONLY,
        max_queued_incoming_messages: int | None = None,
        max_queued_outgoing_messages: int | None = None,
        max_inflight_messages: int | None = None,
        max_concurrent_outgoing_calls: int | None = None,
        properties: mqtt.Properties | None = None,
        tls_context: ssl.SSLContext | None = None,
        tls_params: TLSParameters | None = None,
        tls_insecure: bool | None = None,
        proxy: ProxySettings | None = None,
        socket_options: Iterable[SocketOption] | None = None,
        websocket_path: str | None = None,
        websocket_headers: WebSocketHeaders | None = None,
        routers: Sequence[MQTTRouter] | None = None,
    ):
        super().__init__()
        self.client = MQTTClient(
            hostname,
            port,
            username=username,
            password=password,
            logger=logger,
            identifier=identifier,
            queue_type=queue_type,
            protocol=ProtocolVersion.V5,
            will=will,
            clean_session=clean_session,
            transport=transport,
            timeout=timeout,
            keepalive=keepalive,
            bind_address=bind_address,
            bind_port=bind_port,
            clean_start=clean_start,
            max_queued_incoming_messages=max_queued_incoming_messages,
            max_queued_outgoing_messages=max_queued_outgoing_messages,
            max_inflight_messages=max_inflight_messages,
            max_concurrent_outgoing_calls=max_concurrent_outgoing_calls,
            properties=properties,
            tls_context=tls_context,
            tls_params=tls_params,
            tls_insecure=tls_insecure,
            proxy=proxy,
            socket_options=socket_options,
            websocket_path=websocket_path,
            websocket_headers=websocket_headers,
        )
        self._subscriptions_map: dict[int, Subscription] = {}
        self._sub_manager = SubscriptionManager(self)
        self._message_handler = MessageHandler(self)
        self._state: dict[str, Any] = {}

        if routers is not None:
            for router in routers:
                self.include_router(router)

    @property
    def identifier(self) -> str:
        return self.client.identifier

    def __setitem__(self, key: str, value: Any) -> None:
        self._state[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._state[key]

    def __delitem__(self, key: str) -> None:
        del self._state[key]

    async def __aenter__(self):
        self._started = True
        await self.client.__aenter__()
        await self._message_handler.__aenter__()
        await self.subscribe_all()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.client.__aexit__(exc_type, exc_value, traceback)
        await self._message_handler.__aexit__(exc_type, exc_value, traceback)

    async def subscribe_all(self) -> None:
        await self._sub_manager.subscribe_all()

    async def publish(
        self,
        topic: str,
        payload: PayloadType = None,
        qos: int = 0,
        retain: bool = False,
        properties: dict[str, Any] | None = None,
    ) -> None:
        mqtt_properties = None
        if properties is not None:
            mqtt_properties = properties_from_dict(properties, PacketTypes.PUBLISH)

        await self.client.publish(
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain,
            properties=mqtt_properties,
        )

    def response_context(
        self,
        response_topic: str,
        qos: int = 0,
        default_timeout: float | None = 60,
        **kwargs,
    ) -> ResponseContext:
        return ResponseContext(
            self,
            response_topic,
            qos,
            default_timeout,
            **kwargs,
        )
