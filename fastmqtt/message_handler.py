import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING

from .exceptions import FastMQTTError
from .structures import Message
from .subscription_manager import Subscription

if TYPE_CHECKING:
    from .fastmqtt import FastMQTT

log = logging.getLogger(__name__)


class MessageHandler:
    def __init__(self, fastmqtt: "FastMQTT"):
        self.fastmqtt = fastmqtt
        self._messages_handler_lock = asyncio.Lock()
        self._messages_handler_task = None

    async def __aenter__(self):
        self._messages_handler_task = asyncio.create_task(self._messages_handler())
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        if self._messages_handler_task is None:
            return

        self._messages_handler_task.cancel()

        with contextlib.suppress(asyncio.CancelledError):
            await self._messages_handler_task

        self._messages_handler_task = None

    async def _wrap_message(
        self,
        subscription: Subscription,
        message: Message,
    ) -> None:
        results = await asyncio.gather(*(callback(message) for callback in subscription.callbacks))
        response_topic = message.properties.get("ResponseTopic")

        response_properties = None
        if "CorrelationData" in message.properties:
            response_properties = {"CorrelationData": message.properties["CorrelationData"]}

        for result in results:
            if result is not None and response_topic is None:
                raise FastMQTTError("Callback returned result, but message has no response_topic")

            if response_topic is not None:
                await self.fastmqtt.publish(
                    response_topic,
                    result,
                    properties=response_properties,
                )

    async def _messages_handler(self) -> None:
        if self._messages_handler_lock.locked():
            raise FastMQTTError("Messages handler is already running")

        async with self._messages_handler_lock:
            while True:
                try:
                    async for message in self.fastmqtt.client.messages:
                        message = Message._from_aiomqtt_message(self.fastmqtt, message)
                        if "SubscriptionIdentifier" not in message.properties:
                            log.warning(
                                "Message has no SubscriptionIdentifier (%s)",
                                message.topic,
                            )
                            continue

                        identifiers = message.properties["SubscriptionIdentifier"]

                        for identifier in identifiers:
                            subscription = self.fastmqtt._subscriptions_map.get(identifier)

                            if subscription is None:
                                log.error(
                                    "Message has unknown SubscriptionIdentifier %s (%s)",
                                    identifier,
                                    message.topic,
                                )
                                continue

                            asyncio.create_task(self._wrap_message(subscription, message))

                except asyncio.CancelledError:
                    return

                except Exception as e:
                    log.exception("Error in messages handler: %s", e)
