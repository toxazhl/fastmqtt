**README.md**

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
from fastmqtt import FastMQTT, MQTTRouter

router = MQTTRouter()

@router.on_message("my/topic")  # Subscribe and handle incoming messages
async def message_handler(message: Message, properties: dict):
    print(f"Message received: {message.payload.decode()} on topic {message.topic}")

async def main():
    client = FastMQTT("mqtt.example.com", routers=[router]) 

    async with client:  # Connect and automatically handle subscriptions
        await client.publish("my/topic", "Hello from FastMQTT!")
        await asyncio.sleep(5)  # Keep running for a bit 

if __name__ == "__main__":
    asyncio.run(main())
```

**Request-Response Example**

```python
@router.on_message("temperature/request")
async def temp_request_handler(message: Message, properties: dict):
    # Simulate getting a temperature reading
    return 25  # Return the temperature

async def main():
    client = FastMQTT("mqtt.example.com", routers=[router])

    async with client:
        async with client.response_context(f"temperature/response/{client.identifier}") as ctx:
            response = await ctx.request("temperature/request")
            print(f"Temperature: {response.payload.decode()}") 
```

**Contributions**

We welcome contributions to improve FastMQTT! Please open issues for bug reports or feature suggestions, and fork the repository to submit pull requests.

Let me know if you'd like modifications or have specific aspects you want to emphasize in the README! 
