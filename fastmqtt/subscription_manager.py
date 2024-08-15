import asyncio

from .connectors import BaseConnector
from .exceptions import FastMqttError
from .properties import SubscribeProperties
from .types import CallbackType, Subscription


class IdentifierManager:
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
        self._identifier_manager = IdentifierManager()
        self._subscriptions_map: dict[int, Subscription] = {}

    def get_subscription(self, identifier: int) -> Subscription | None:
        return self._subscriptions_map.get(identifier)

    async def subscribe(self, subscription: Subscription) -> int:
        identifier = self._identifier_manager.get_id()
        properties = SubscribeProperties(subscription_identifier=identifier)
        await self._connector.subscribe(
            topic=subscription.topic,
            options=subscription.options,
            properties=properties,
        )

        self._subscriptions_map[identifier] = subscription
        return identifier

    async def subscribe_multiple(self, subscriptions: list[Subscription]) -> list[int]:
        if self._identifier_manager.get_available_count() < len(subscriptions):
            raise FastMqttError("Not enough subscription identifiers available")

        await asyncio.sleep(0.1)
        return await asyncio.gather(
            *[self.subscribe(subscription) for subscription in subscriptions]
        )

    async def unsubscribe(self, identifier: int, callback: CallbackType | None = None) -> None:
        subscription = self._subscriptions_map.get(identifier)
        if subscription is None:
            raise FastMqttError(f"Unknown subscription identifier {identifier}")

        if callback is not None:
            subscription.callbacks.remove(callback)

        if callback is None or not subscription.callbacks:
            await self._connector.unsubscribe(topic=subscription.topic)
            self._subscriptions_map.pop(identifier, None)
            self._identifier_manager.put_back(identifier)
