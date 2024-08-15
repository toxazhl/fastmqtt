import asyncio
import logging

from fastmqtt import FastMQTT, Message, MQTTRouter

logging.basicConfig(level=logging.INFO)


router = MQTTRouter()


@router.on_message("my/topic/1")  # Subscribe and handle incoming messages
async def message_handler(message: Message):
    print(f"Message received: {message.payload.decode()} on topic {message.topic}")


async def main():
    fastmqtt = FastMQTT("test.mosquitto.org")
    fastmqtt.include_router(router)  # or pass routers=[router] to FastMQTT

    async with fastmqtt:
        # Publish a message to a topic
        await fastmqtt.publish("my/topic/1", "Hello from FastMQTT!")

        await asyncio.sleep(5)  # Keep running for a bit


if __name__ == "__main__":
    asyncio.run(main())
