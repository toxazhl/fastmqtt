# FastMqtt

A performant, flexible, and user-friendly MQTT client library built on top of aiomqtt. FastMqtt simplifies message handling, advanced subscriptions, and convenient request-response patterns within the MQTT protocol.

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

from fastmqtt import FastMqtt, Message

fastmqtt = FastMqtt("test.mosquitto.org")


# Use decorator to subscribe to a topic before connecting
@fastmqtt.on_message("my/topic/1")  # Subscribe and handle incoming messages
async def message_handler(message: Message):
    print(f"Message received: {message.payload.text()} on topic {message.topic}")


async def main():
    # Use register method to subscribe to a topic before connecting
    fastmqtt.register(message_handler, "my/topic/2")
    async with fastmqtt:  # Connect and automatically subscribe to registered topics
        # Use subscribe method to subscribe to a topic after connecting
        await fastmqtt.subscribe(message_handler, "my/topic/3")

        # Publish a message to a topic
        await fastmqtt.publish("my/topic/1", "Hello from FastMqtt!")
        await fastmqtt.publish("my/topic/2", "Hello from FastMqtt!")
        await fastmqtt.publish("my/topic/3", "Hello from FastMqtt!")
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())

```

**Contributions**

We welcome contributions to improve FastMqtt! Please open issues for bug reports or feature suggestions, and fork the repository to submit pull requests.

Let me know if you'd like modifications or have specific aspects you want to emphasize in the README! 
