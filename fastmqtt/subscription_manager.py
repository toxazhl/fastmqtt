import asyncio

from .connectors import BaseConnector
from .exceptions import FastMQTTError
from .properties import SubscribeProperties
from .types import CallbackType, Subscription, SubscriptionWithId


class IdManager:
    def __init__(self, max_id: int = 268435455):
        self.max_id = max_id
        self.current_id = 0
        self.available_ids = set()
        self.used_ids = set()

    def get_id(self):
        if self.available_ids:
            return self.available_ids.pop()

        if self.current_id < self.max_id:
            self.current_id += 1
            self.used_ids.add(self.current_id)
            return self.current_id

        raise ValueError("No more IDs available")

    def put_back(self, id_: int):
        if id_ in self.used_ids:
            self.used_ids.remove(id_)
            self.available_ids.add(id_)
        else:
            raise ValueError(f"ID {id_} is not in use")

    def get_available_count(self):
        return len(self.available_ids) + (self.max_id - self.current_id)

    def get_used_count(self):
        return len(self.used_ids)


class SubscriptionManager:
    def __init__(self, connector: BaseConnector):
        self._connector = connector
        self._id_manager = IdManager()
        self._id_to_subscription: dict[int, SubscriptionWithId] = {}

    def get_subscription(self, identifier: int) -> SubscriptionWithId | None:
        return self._id_to_subscription.get(identifier)

    async def subscribe(self, subscription: Subscription) -> SubscriptionWithId:
        identifier = self._id_manager.get_id()
        await self._connector.subscribe(
            topic=subscription.topic,
            options=subscription.options,
            properties=SubscribeProperties(
                subscription_identifier=identifier,
            ),
        )

        subscription_with_id = SubscriptionWithId(
            callbacks=subscription.callbacks,
            topic=subscription.topic,
            options=subscription.options,
            id=identifier,
        )
        self._id_to_subscription[identifier] = subscription_with_id
        return subscription_with_id

    async def subscribe_multiple(
        self, subscriptions: list[Subscription]
    ) -> list[SubscriptionWithId]:
        if self._id_manager.get_available_count() < len(subscriptions):
            raise FastMQTTError("Not enough subscription identifiers available")

        await asyncio.sleep(0.1)
        return await asyncio.gather(
            *[self.subscribe(subscription) for subscription in subscriptions]
        )

    async def unsubscribe(
        self,
        identifier: int | None = None,
        topic: str | None = None,
        subscription: SubscriptionWithId | None = None,
        callback: CallbackType | None = None,
    ) -> None:
        if len([arg for arg in [identifier, topic, subscription] if arg is not None]) != 1:
            raise ValueError(
                "Exactly one of arguments (identifier, topic or subscription) must be provided"
            )

        if identifier is not None:
            subscription = self._id_to_subscription.get(identifier)
        if topic is not None:
            subscription = next(
                (sub for sub in self._id_to_subscription.values() if sub.topic == topic),
                None,
            )

        if subscription is None:
            raise FastMQTTError("Subscription not found")

        if callback is not None:
            subscription.callbacks.remove(callback)

        if callback is None or not subscription.callbacks:
            await self._connector.unsubscribe(topic=subscription.topic)
            self._id_to_subscription.pop(subscription.id, None)
            self._id_manager.put_back(subscription.id)
