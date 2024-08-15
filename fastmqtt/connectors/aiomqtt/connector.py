import asyncio
import contextlib
import logging
import ssl
from functools import wraps
from typing import Callable, Iterable, Literal

import aiomqtt
import paho.mqtt.client
import paho.mqtt.enums
from aiomqtt import ProxySettings, TLSParameters, Will
from aiomqtt.types import SocketOption
from tenacity import RetryCallState, retry, wait_exponential

from fastmqtt.connectors.base import BaseConnector
from fastmqtt.properties import (
    ConnectProperties,
    PublishProperties,
    SubscribeProperties,
    UnsubscribeProperties,
)
from fastmqtt.types import CleanStart, PayloadType, SubscribeOptions

from .convertors.message import aiomqtt_to_fastmqtt_message
from .convertors.options import fastmqtt_to_paho_subscribe_options
from .convertors.properties import fastmqtt_to_paho_properties

logger = logging.getLogger(__name__)
WebSocketHeaders = dict[str, str] | Callable[[dict[str, str]], dict[str, str]]


def on_reconnect_log(retry_state: RetryCallState) -> None:
    if retry_state.outcome is None:
        raise RuntimeError("log_it() called before outcome was set")

    if retry_state.next_action is None:
        raise RuntimeError("log_it() called before next_action was set")

    if retry_state.outcome.failed:
        ex = retry_state.outcome.exception()
        verb, value = "raised", f"{ex.__class__.__name__}: {ex}"

    else:
        verb, value = "returned", retry_state.outcome.result()

    logger.warning(
        f"Reconnecting in {retry_state.next_action.sleep} seconds, as it {verb} {value}"
    )


def retry_disconected(max_retries: int = 3):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            self: AiomqttConnector = args[0]
            last_error = None
            for _ in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except aiomqtt.exceptions.MqttCodeError as e:
                    last_error = e
                    if e.rc != paho.mqtt.client.MQTT_ERR_NO_CONN:
                        raise

                    await self.reconnect_event.wait()

            raise RuntimeError(f"Max retries exceeded {max_retries}, last error: {last_error}")

        return wrapper

    return decorator


class AiomqttConnector(BaseConnector):
    def __init__(
        self,
        hostname: str,
        port: int,
        username: str | None = None,
        password: str | None = None,
        client_id: str | None = None,
        will: Will | None = None,
        keepalive: int = 60,
        properties: ConnectProperties | None = None,
        transport: Literal["tcp", "websockets"] | None = None,
        timeout: float | None = None,
        bind_address: str | None = None,
        bind_port: int | None = None,
        clean_start: CleanStart = CleanStart.FIRST_ONLY,
        max_queued_incoming_messages: int | None = None,
        max_queued_outgoing_messages: int | None = None,
        max_inflight_messages: int | None = None,
        max_concurrent_outgoing_calls: int | None = None,
        tls_context: ssl.SSLContext | None = None,
        tls_params: TLSParameters | None = None,
        tls_insecure: bool | None = None,
        proxy: ProxySettings | None = None,
        socket_options: Iterable[SocketOption] | None = None,
        websocket_path: str | None = None,
        websocket_headers: WebSocketHeaders | None = None,
    ):
        self._aiomqtt_kwargs = {
            "hostname": hostname,
            "port": port,
            "username": username,
            "password": password,
            "identifier": client_id,
            "protocol": paho.mqtt.enums.MQTTProtocolVersion.MQTTv5,
            "will": will,
            "transport": transport,
            "timeout": timeout,
            "keepalive": keepalive,
            "bind_address": bind_address,
            "bind_port": bind_port,
            "max_queued_incoming_messages": max_queued_incoming_messages,
            "max_queued_outgoing_messages": max_queued_outgoing_messages,
            "max_inflight_messages": max_inflight_messages,
            "max_concurrent_outgoing_calls": max_concurrent_outgoing_calls,
            "properties": properties and fastmqtt_to_paho_properties(properties),
            "tls_context": tls_context,
            "tls_params": tls_params,
            "tls_insecure": tls_insecure,
            "proxy": proxy,
            "socket_options": socket_options,
            "websocket_path": websocket_path,
            "websocket_headers": websocket_headers,
        }
        self._aiomqtt_kwargs = {k: v for k, v in self._aiomqtt_kwargs.items() if v is not None}
        self._aiomqtt_client: aiomqtt.Client | None = None

        self._maintain_connection_task: asyncio.Task | None = None

        super().__init__(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            client_id=client_id,
            will=will,
            keepalive=keepalive,
            properties=properties,
            clean_start=clean_start,
        )

    def _on_connect(self) -> None:
        self.connected_event.set()
        self.disconnected_event.clear()
        self.reconnect_event.set()
        self.reconnect_event.clear()
        asyncio.gather(*[cb() for cb in self._connect_callbacks])

    def _on_disconnect(self) -> None:
        self.connected_event.clear()
        self.disconnected_event.set()
        asyncio.gather(*[cb() for cb in self._disconnect_callbacks])

    async def _get_client(self) -> aiomqtt.Client:
        await self.connected_event.wait()
        if self._aiomqtt_client is None:
            raise RuntimeError("Client is not set")

        return self._aiomqtt_client

    @retry_disconected()
    async def subscribe(
        self,
        topic: str,
        options: SubscribeOptions | None = None,
        properties: SubscribeProperties | None = None,
    ) -> None:
        paho_options = None
        paho_properties = None
        if options is not None:
            paho_options = fastmqtt_to_paho_subscribe_options(options)
        if properties is not None:
            paho_properties = fastmqtt_to_paho_properties(properties)

        client = await self._get_client()
        await client.subscribe(
            topic=topic,
            options=paho_options,
            properties=paho_properties,
        )

    @retry_disconected()
    async def subscribe_multiple(
        self,
        topics: list[tuple[str, SubscribeOptions]],
        properties: SubscribeProperties | None = None,
    ) -> None:
        paho_properties = None
        paho_topics = []
        if properties is not None:
            paho_properties = fastmqtt_to_paho_properties(properties)
        for topic, options in topics:
            paho_topics.append((topic, fastmqtt_to_paho_subscribe_options(options)))

        client = await self._get_client()
        await client.subscribe(
            topic=paho_topics,
            properties=paho_properties,
        )

    @retry_disconected()
    async def unsubscribe(
        self,
        topic: str,
        properties: SubscribeProperties | None = None,
    ) -> None:
        paho_properties = None
        if properties is not None:
            paho_properties = fastmqtt_to_paho_properties(properties)

        client = await self._get_client()
        await client.unsubscribe(topic=topic, properties=paho_properties)

    @retry_disconected()
    async def unsubscribe_multiple(
        self,
        topics: list[str],
        properties: UnsubscribeProperties | None = None,
    ) -> None:
        paho_properties = None
        if properties is not None:
            paho_properties = fastmqtt_to_paho_properties(properties)

        client = await self._get_client()
        await client.unsubscribe(topic=topics, properties=paho_properties)

    @retry_disconected()
    async def publish(
        self,
        topic: str,
        payload: PayloadType = None,
        qos: int = 0,
        retain: bool = False,
        properties: PublishProperties | None = None,
    ) -> None:
        paho_properties = None
        if properties is not None:
            paho_properties = fastmqtt_to_paho_properties(properties)

        client = await self._get_client()
        await client.publish(
            topic=topic,
            payload=payload,
            qos=qos,
            retain=retain,
            properties=paho_properties,
        )

    async def connect(self) -> None:
        self._maintain_connection_task = asyncio.create_task(self._maintain_connection())
        await self.connected_event.wait()

    async def disconnect(self) -> None:
        if self._maintain_connection_task is not None:
            self._maintain_connection_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._maintain_connection_task

        await self.disconnected_event.wait()

    @retry(
        wait=wait_exponential(multiplier=0.1, max=5, exp_base=2.5), before_sleep=on_reconnect_log
    )
    async def _maintain_connection(self) -> None:
        clean_start = self._clean_start == CleanStart.ALWAYS or (
            self._first_connect and self._clean_start == CleanStart.FIRST_ONLY
        )

        async with aiomqtt.Client(clean_start=clean_start, **self._aiomqtt_kwargs) as client:
            try:
                if self._first_connect:
                    logger.info(
                        "Connected to %s as %s",
                        f"{self._hostname}:{self._port}",
                        self.identifier,
                    )
                else:
                    logger.info(
                        "Connection established to %s as %s",
                        f"{self._hostname}:{self._port}",
                        self.identifier,
                    )

                self._first_connect = False
                self._aiomqtt_client = client
                self._on_connect()
                await self._process_messages(client)

            finally:
                self._aiomqtt_client = None
                self._on_disconnect()

    async def _process_messages(self, client: aiomqtt.Client) -> None:
        async for aiomqtt_message in client.messages:
            fastmqtt_message = aiomqtt_to_fastmqtt_message(aiomqtt_message)
            asyncio.gather(*[cb(fastmqtt_message) for cb in self._message_callbacks])
