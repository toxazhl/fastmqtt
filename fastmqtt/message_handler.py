import asyncio
import logging
from typing import TYPE_CHECKING, Any

from .connectors import BaseConnector
from .encoders import BaseDecoder
from .exceptions import FastMQTTError
from .properties import PublishProperties
from .subscription_manager import Subscription, SubscriptionManager
from .types import Message, Payload, RawMessage

if TYPE_CHECKING:
    from .fastmqtt import FastMQTT

log = logging.getLogger(__name__)


class MessageHandler:
    def __init__(
        self,
        fastmqtt: "FastMQTT",
        connector: BaseConnector,
        subscription_manager: SubscriptionManager,
        payload_decoder: BaseDecoder,
    ) -> None:
        self._fastmqtt = fastmqtt
        self._connector = connector
        self._subscription_manager = subscription_manager
        self._payload_decoder = payload_decoder

        self._connector.add_message_callback(self.on_message)

    async def on_message(self, raw_message: RawMessage) -> None:
        message = Message(
            topic=raw_message.topic,
            payload=Payload(data=raw_message.payload, decoder=self._payload_decoder),
            qos=raw_message.qos,
            retain=raw_message.retain,
            mid=raw_message.mid,
            properties=raw_message.properties,
            client=self._fastmqtt,
        )

        if message.properties.subscription_identifier is None:
            log.warning(f"Message has no subscription_identifier {raw_message}")
            return

        for id_ in message.properties.subscription_identifier:
            subscription = self._subscription_manager.get_subscription(id_)

            if subscription is None:
                log.error(f"Message has unknown subscription_identifier {id_} ({message.topic})")
                continue

            asyncio.create_task(self._process_message(subscription, message))

    async def _handle_result(self, result: Any, message: Message) -> None:
        if result is None:
            return

        if message.properties.response_topic is None:
            raise FastMQTTError("Callback returned result, but message has no response_topic")

        response_properties = None
        if message.properties.correlation_data is not None:
            response_properties = PublishProperties(
                correlation_data=message.properties.correlation_data
            )

        await self._fastmqtt.publish(
            topic=message.properties.response_topic,
            payload=result,
            properties=response_properties,
        )

    async def _process_message(self, subscription: Subscription, message: Message) -> None:
        callback_tasks = (
            asyncio.create_task(callback(message)) for callback in subscription.callbacks
        )
        for result in asyncio.as_completed(callback_tasks):
            try:
                result = await result
            except Exception as e:
                log.exception(f"Error in callback {e}")
                continue

            await self._handle_result(result, message)
