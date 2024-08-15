# FastMQTT

FastMQTT is a high-performance, easy-to-use MQTT v5 client library for Python, built on top of asyncio. It provides a simple and intuitive API for working with MQTT, offering features like automatic reconnection, custom encoders/decoders, and full support for MQTT v5 capabilities.

## Features

- Full support for MQTT v5
- Asynchronous API based on asyncio
- Automatic reconnection
- Flexible subscription management
- Custom payload encoders and decoders
- Request-response pattern support
- Router-based topic handling

## Installation

Install FastMQTT using pip:

```bash
pip install fastmqtt
```

## Usage Guide

### Basic Usage

Here's a simple example demonstrating how to use FastMQTT:

```python
import asyncio
import logging
from fastmqtt import FastMQTT, Message

logging.basicConfig(level=logging.INFO)

fastmqtt = FastMQTT("test.mosquitto.org")

@fastmqtt.on_message("my/topic/1")
async def message_handler(message: Message):
    print(f"Message received: {message.payload.decode()} on topic {message.topic}")

async def main():
    async with fastmqtt:
        await fastmqtt.publish("my/topic/1", "Hello from FastMQTT!")
        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
```

### Subscription Management

FastMQTT offers multiple ways to manage subscriptions:

1. Using the `@on_message` decorator, only before connecting:

```python
@fastmqtt.on_message("my/topic")
async def handler(message: Message):
    ...
```

2. Using the `register` method before connecting, only before connecting:

```python
fastmqtt.register(handler, "my/topic")
```

3. Using the `subscribe` method after connecting, only after connecting:

```python
await fastmqtt.subscribe(handler, "my/topic")
```

### Router-based Topic Handling

For better organization of your MQTT handlers, use the `MQTTRouter`:

```python
from fastmqtt import MQTTRouter

router = MQTTRouter()

@router.on_message("my/topic")
async def handler(message: Message):
    ...

fastmqtt = FastMQTT("test.mosquitto.org", routers=[router])
```

### Custom Encoders and Decoders

FastMQTT supports custom payload encoding and decoding:

```python
from fastmqtt.encoders import JsonEncoder, JsonDecoder

fastmqtt = FastMQTT(
    "test.mosquitto.org",
    payload_encoder=JsonEncoder(),
    payload_decoder=JsonDecoder()
)

# Now you can publish and receive JSON payloads
await fastmqtt.publish("my/topic", {"key": "value"})
```

### Request-Response Pattern

FastMQTT provides a convenient way to implement request-response patterns:

```python
async with fastmqtt.response_context("response/topic") as ctx:
    response = await ctx.request("request/topic", "Hello")
    print(f"Response: {response.payload.decode()}")
```

### MQTT v5 Features

FastMQTT fully supports MQTT v5 features. Here are some examples:

1. Using MQTT v5 properties:

```python
from fastmqtt.properties import PublishProperties

props = PublishProperties(
    content_type="application/json",
    user_property=[("key", "value")]
)
await fastmqtt.publish("my/topic", payload, properties=props)
```

2. Handling retained messages:

```python
from fastmqtt.types import RetainHandling

@fastmqtt.on_message("my/topic", retain_handling=RetainHandling.DO_NOT_SEND)
async def handler(message: Message):
    ...
```

3. Working with shared subscriptions:

```python
@fastmqtt.on_message("$share/group/my/topic")
async def shared_handler(message: Message):
    ...
```


## Contributing

Contributions to FastMQTT are welcome! Please follow these steps to contribute:

1. Fork the repository
2. Create a new branch for your feature or bug fix
3. Write your code and tests
4. Run the example scripts to ensure everything passes
5. Submit a pull request with a clear description of your changes


## License

FastMQTT is released under the MIT License. See the [LICENSE](LICENSE) file for details.