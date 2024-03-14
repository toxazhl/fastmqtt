import asyncio

from fastmqtt import FastMQTT, Message, MQTTRouter

router = MQTTRouter()


@router.on_message("my/topic")
async def message_handler(message: Message):
    database = message.fastmqtt["database"]
    ...


async def main():
    fastmqtt = FastMQTT("test.mosquitto.org", routers=[router])
    fastmqtt["database"] = "my_database"  # Pass some data to message handlers

    async with fastmqtt:
        await fastmqtt.publish("my/topic", "Hello from FastMQTT!")
        await asyncio.sleep(5)  # Keep running for a bit


if __name__ == "__main__":
    asyncio.run(main())
