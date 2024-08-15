from typing import Any, Callable, Sequence, Type

from .connectors import AiomqttConnector, BaseConnector
from .encoders import BaseDecoder, BaseEncoder, NoneDecoder, NoneEncoder
from .message_handler import MessageHandler
from .properties import ConnectProperties, PublishProperties
from .response import ResponseContext
from .router import MQTTRouter
from .subscription_manager import CallbackType, SubscriptionManager
from .types import RetainHandling, SubscribeOptions, SubscriptionWithId

WebSocketHeaders = dict[str, str] | Callable[[dict[str, str]], dict[str, str]]


class FastMQTT(MQTTRouter):
    def __init__(
        self,
        hostname: str,
        port: int = 1883,
        username: str | None = None,
        password: str | None = None,
        client_id: str | None = None,
        will=None,
        keepalive=60,
        properties: ConnectProperties | None = None,
        connector_type: Type[BaseConnector] = AiomqttConnector,
        routers: Sequence[MQTTRouter] | None = None,
        default_subscribe_options: SubscribeOptions | None = None,
        payload_encoder: BaseEncoder = NoneEncoder(),
        payload_decoder: BaseDecoder = NoneDecoder(),
    ):
        super().__init__(default_subscribe_options=default_subscribe_options)
        self._payload_encoder = payload_encoder
        self._payload_decoder = payload_decoder

        self._connector = connector_type(
            hostname=hostname,
            port=port,
            username=username,
            password=password,
            client_id=client_id,
            will=will,
            keepalive=keepalive,
            properties=properties,
        )
        self._subscription_manager = SubscriptionManager(self._connector)
        self._message_handler = MessageHandler(
            self, self._connector, self._subscription_manager, self._payload_decoder
        )
        self._state: dict[str, Any] = {}

        # self._connector.add_connect_callback(self.subscribe_all)
        self._routers = routers or []
        for router in self._routers:
            self.include_router(router)

    @property
    def client_id(self) -> str:
        return self._connector._client_id

    def __setitem__(self, key: str, value: Any) -> None:
        self._state[key] = value

    def __getitem__(self, key: str) -> Any:
        return self._state[key]

    def __delitem__(self, key: str) -> None:
        del self._state[key]

    def get(self, key: str, /, default: Any = None) -> Any:
        return self._state.get(key, default)

    async def connect(self) -> None:
        await self._connector.connect()
        await self.subscribe_all()

    async def disconnect(self) -> None:
        await self._connector.disconnect()

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    async def subscribe(
        self,
        callback: CallbackType,
        topic: str,
        qos: int | None = None,
        no_local: bool | None = None,
        retain_as_published: bool | None = None,
        retain_handling: RetainHandling | None = None,
    ) -> SubscriptionWithId:
        subscription = self._register(
            callback=callback,
            topic=topic,
            qos=qos,
            no_local=no_local,
            retain_as_published=retain_as_published,
            retain_handling=retain_handling,
        )
        if len(subscription.callbacks) == 1:
            # Only subscribe if it's the first callback
            return await self._subscription_manager.subscribe(subscription)

        # TODO: Refactor it
        return next(
            (
                sub
                for sub in self._subscription_manager._id_to_subscription.values()
                if sub.topic == topic and sub.callbacks == subscription.callbacks
            ),
        )

    async def subscribe_all(self) -> list[SubscriptionWithId]:
        self._subscribed = True
        return await self._subscription_manager.subscribe_multiple(self._subscriptions)

    async def unsubscribe(
        self,
        identifier: int | None = None,
        topic: str | None = None,
        subscription: SubscriptionWithId | None = None,
        callback: CallbackType | None = None,
    ) -> None:
        await self._subscription_manager.unsubscribe(
            identifier=identifier, topic=topic, subscription=subscription, callback=callback
        )

    async def publish(
        self,
        topic: str,
        payload: Any = None,
        qos: int = 0,
        retain: bool = False,
        properties: PublishProperties | None = None,
    ) -> None:
        await self._connector.publish(
            topic=topic,
            payload=self._payload_encoder(payload),
            qos=qos,
            retain=retain,
            properties=properties,
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
