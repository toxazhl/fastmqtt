import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Any

import aiomqtt

from .exceptions import FastMQTTError
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
        message: aiomqtt.Message,
        properties: dict[str, Any],
    ) -> None:
        results = await asyncio.gather(
            *(callback(message, properties) for callback in subscription.callbacks)
        )
        response_properties = None
        response_topic = properties.get("ResponseTopic")
        correlation_data = properties.get("CorrelationData")
        if correlation_data is not None:
            correlation_data_new = bytes.fromhex(correlation_data)
            response_properties = {"CorrelationData": correlation_data_new}

        if any(results) and response_topic is None:
            raise FastMQTTError("Callback returned result, but message has no response_topic")

        if response_topic is not None:
            for result in results:
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
                        if message.properties is None:
                            log.error("Message has no properties (%s)", message.topic)
                            continue

                        properties = message.properties.json()
                        identifiers = properties.get("SubscriptionIdentifier")
                        if not identifiers:
                            log.warning(
                                "Message has no SubscriptionIdentifier (%s)",
                                message.topic,
                            )
                            continue

                        for identifier in identifiers:
                            subscription = self.fastmqtt.subscriptions_map.get(identifier)

                            if subscription is None:
                                log.error(
                                    "Message has unknown SubscriptionIdentifier %s (%s)",
                                    identifier,
                                    message.topic,
                                )
                                continue

                            asyncio.create_task(
                                self._wrap_message(subscription, message, properties)
                            )

                except asyncio.CancelledError:
                    return

                except Exception as e:
                    log.exception("Error in messages handler: %s", e)
