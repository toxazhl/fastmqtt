import paho.mqtt.subscribeoptions

from fastmqtt.types import SubscribeOptions


def fastmqtt_to_paho_subscribe_options(
    options: SubscribeOptions,
) -> paho.mqtt.subscribeoptions.SubscribeOptions:
    return paho.mqtt.subscribeoptions.SubscribeOptions(
        qos=options.qos,
        noLocal=options.no_local,
        retainAsPublished=options.retain_as_published,
        retainHandling=options.retain_handling,
    )


def paho_to_fastmqtt_subscribe_options(
    options: paho.mqtt.subscribeoptions.SubscribeOptions,
) -> SubscribeOptions:
    return SubscribeOptions(
        qos=options.QoS,  # type: ignore
        no_local=options.noLocal,
        retain_as_published=options.retainAsPublished,
        retain_handling=options.retainHandling,  # type: ignore
    )
