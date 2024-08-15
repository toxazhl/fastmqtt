import logging
from typing import Any, Callable

from .exceptions import FastMQTTError
from .types import CallbackType, RetainHandling, SubscribeOptions, Subscription

log = logging.getLogger(__name__)


def merge_default_subscribe_options(
    default_options: SubscribeOptions,
    new_qos: int | None = None,
    new_no_local: bool | None = None,
    new_retain_as_published: bool | None = None,
    new_retain_handling: RetainHandling | None = None,
) -> SubscribeOptions:
    return SubscribeOptions(
        qos=new_qos or default_options.qos,
        no_local=new_no_local or default_options.no_local,
        retain_as_published=new_retain_as_published or default_options.retain_as_published,
        retain_handling=new_retain_handling or default_options.retain_handling,
    )


def merge_subscribe_options(
    options_exist: SubscribeOptions,
    options_new: SubscribeOptions,
) -> None:
    options_exist.qos = max(options_exist.qos, options_new.qos)

    if options_exist.no_local != options_new.no_local:
        raise FastMQTTError("Different no_local options")
    if options_exist.retain_as_published != options_new.retain_as_published:
        raise FastMQTTError("Different retain_as_published options")
    if options_exist.retain_handling != options_new.retain_handling:
        raise FastMQTTError("Different retain_handling options")


class MQTTRouter:
    def __init__(self, default_subscribe_options: SubscribeOptions | None = None):
        if default_subscribe_options is None:
            default_subscribe_options = SubscribeOptions()

        self._default_subscribe_options = default_subscribe_options
        self._subscriptions: list[Subscription] = []
        self._included = False

    def _register(
        self,
        callback: CallbackType,
        topic: str,
        qos: int | None = None,
        no_local: bool | None = None,
        retain_as_published: bool | None = None,
        retain_handling: RetainHandling | None = None,
    ) -> Subscription:
        subscribe_options = merge_default_subscribe_options(
            self._default_subscribe_options,
            qos,
            no_local,
            retain_as_published,
            retain_handling,
        )

        for subscription in self._subscriptions:
            if str(subscription.topic) == topic:
                subscription.callbacks.append(callback)
                merge_subscribe_options(subscription.options, subscribe_options)
                return subscription

        subscription = Subscription(
            [callback],
            topic,
            subscribe_options,
        )

        self._subscriptions.append(subscription)

        return subscription

    def register(
        self,
        callback: CallbackType,
        topic: str,
        qos: int | None = None,
        no_local: bool | None = None,
        retain_as_published: bool | None = None,
        retain_handling: RetainHandling | None = None,
    ) -> Subscription:
        if self._included:
            raise FastMQTTError(
                "Cannot register new subscriptions after router is included, "
                "use fastmqtt.subscribe instead"
            )

        return self._register(
            callback=callback,
            topic=topic,
            qos=qos,
            no_local=no_local,
            retain_as_published=retain_as_published,
            retain_handling=retain_handling,
        )

    def on_message(
        self,
        topic: str,
        qos: int | None = None,
        no_local: bool | None = None,
        retain_as_published: bool | None = None,
        retain_handling: RetainHandling | None = None,
    ) -> Callable[..., Any]:
        def wrapper(func: CallbackType) -> CallbackType:
            self.register(
                callback=func,
                topic=topic,
                qos=qos,
                no_local=no_local,
                retain_as_published=retain_as_published,
                retain_handling=retain_handling,
            )
            return func

        return wrapper

    def include_router(self, router: "MQTTRouter") -> None:
        if router._default_subscribe_options is None:
            router._default_subscribe_options = self._default_subscribe_options

        subs = self._subscriptions.copy()
        for router_sub in router._subscriptions:
            for sub in subs:
                if sub.topic == router_sub.topic:
                    merge_subscribe_options(sub.options, router_sub.options)
                    sub.callbacks.extend(router_sub.callbacks)
                    break
            else:
                self._subscriptions.append(router_sub)

        router._included = True
