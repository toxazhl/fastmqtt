import itertools
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Any, Awaitable, Callable

import aiomqtt
from paho.mqtt.packettypes import PacketTypes
from paho.mqtt.subscribeoptions import SubscribeOptions

from .exceptions import FastMQTTError
from .structures import Message
from .utils import properties_from_dict

if TYPE_CHECKING:
    from .fastmqtt import FastMQTT


CallbackType = Callable[[Message], Awaitable[Any]]


class Retain(IntEnum):
    SEND_ON_SUBSCRIBE = 0
    SEND_IF_NEW_SUB = 1
    DO_NOT_SEND = 2


@dataclass
class Subscription:
    callbacks: list[CallbackType]
    topic: aiomqtt.Topic
    qos: int = 0
    no_local: bool = False
    retain_as_published: bool = False
    retain_handling: Retain = Retain.SEND_ON_SUBSCRIBE


class SubscriptionManager:
    def __init__(self, fastmqtt: "FastMQTT"):
        self.fastmqtt = fastmqtt
        self.subscription_id_counter = itertools.count(1)

    async def subscribe(self, subscription: Subscription) -> int:
        identifier = next(self.subscription_id_counter)
        properties = properties_from_dict(
            {"SubscriptionIdentifier": identifier},
            PacketTypes.SUBSCRIBE,
        )

        await self.fastmqtt.client.subscribe(
            topic=subscription.topic.value,
            qos=subscription.qos,
            options=SubscribeOptions(
                qos=subscription.qos,
                noLocal=subscription.no_local,
                retainAsPublished=subscription.retain_as_published,
                retainHandling=subscription.retain_handling,
            ),
            properties=properties,
        )
        self.fastmqtt._subscriptions_map[identifier] = subscription
        return identifier

    async def subscribe_all(self) -> None:
        for subscription in self.fastmqtt._subscriptions:
            await self.subscribe(subscription)

    async def unsubscribe(self, identifier: int, callback: CallbackType | None = None) -> None:
        subscription = self.fastmqtt._subscriptions_map.get(identifier)
        if subscription is None:
            raise FastMQTTError(f"Unknown subscription identifier {identifier}")

        if callback is not None:
            subscription.callbacks.remove(callback)

        if callback is None or not subscription.callbacks:
            await self.fastmqtt.client.unsubscribe(subscription.topic.value)
            del self.fastmqtt._subscriptions_map[identifier]
