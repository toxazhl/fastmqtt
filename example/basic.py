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
