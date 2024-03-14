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
