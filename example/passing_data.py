import asyncio
import logging

from fastmqtt import FastMQTT, Message

logging.basicConfig(level=logging.INFO)

fastmqtt = FastMQTT("test.mosquitto.org")


# Use decorator to register subscription to a topic before connecting
@fastmqtt.on_message("my/topic/1")  # Subscribe and handle incoming messages
async def message_handler(message: Message):
    print(f"Message received: {message.payload.decode()} on topic {message.topic}")


async def main():
    # Use register method to register subscription to a topic before connecting
    fastmqtt.register(message_handler, "my/topic/2")
    async with fastmqtt:  # Connect and automatically subscribe to registered topics
        # Use subscribe method to subscribe to a topic after connecting
        await fastmqtt.subscribe(message_handler, "my/topic/3")

        # Publish a message to a topic
        await fastmqtt.publish("my/topic/1", "Hello from FastMQTT!")
        await fastmqtt.publish("my/topic/2", "Hello from FastMQTT!")
        await fastmqtt.publish("my/topic/3", "Hello from FastMQTT!")

        await asyncio.sleep(5)  # Keep running for a bit


if __name__ == "__main__":
    asyncio.run(main())
