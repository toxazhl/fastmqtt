# FastMQTT

A performant, flexible, and user-friendly MQTT client library built on top of aiomqtt. FastMQTT simplifies message handling, advanced subscriptions, and convenient request-response patterns within the MQTT protocol.

**Key Features**

* **Efficient Message Handling:** Streamlined asynchronous message processing.
* **Robust Router:** Define topic-based message routing with QoS, no_local, retain options.
* **Subscription Management:** Effortlessly manage subscriptions, including retained messages.
* **Request-Response Patterns:** Convenient `ResponseContext` for request-response communication over MQTT.
* **Correlation Tracking:** Automatic correlation ID generation to match responses with their requests.
* **aiomqtt Foundation:** Built upon the reliable aiomqtt library for core MQTT functionality.

**Installation**

```bash
pip install fastmqtt
```

**Basic Usage**

```python
import asyncio

from fastmqtt import FastMQTT, Message, MQTTRouter

router = MQTTRouter()


@router.on_message("my/topic")  # Subscribe and handle incoming messages
async def message_handler(message: Message):
    print(f"Message received: {message.payload.text()} on topic {message.topic}")


async def main():
    fastmqtt = FastMQTT("test.mosquitto.org", routers=[router])

    async with fastmqtt:  # Connect and automatically handle subscriptions
        await fastmqtt.publish("my/topic", "Hello from FastMQTT!")
        await asyncio.sleep(5)  # Keep running for a bit


if __name__ == "__main__":
    asyncio.run(main())

```

**Contributions**

We welcome contributions to improve FastMQTT! Please open issues for bug reports or feature suggestions, and fork the repository to submit pull requests.

Let me know if you'd like modifications or have specific aspects you want to emphasize in the README! 
