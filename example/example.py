import asyncio
import json
from typing import Any

from aiomqtt import Message

from fastmqtt import FastMQTT, MQTTRouter, Retain

router = MQTTRouter()


@router.on_message("test/fastmqtt/print_message", retain_handling=Retain.DO_NOT_SEND)
async def on_print_message(message: Message, properties: dict[str, Any]):
    print(f"Received message: {message.payload.decode()}")


@router.on_message("test/fastmqtt/process/substruction", retain_handling=Retain.DO_NOT_SEND)
async def on_process_substruction(message: Message, properties: dict[str, Any]):
    payload = json.loads(message.payload)
    return payload["a"] - payload["b"]


@router.on_message("test/fastmqtt/process/multiplication", retain_handling=Retain.DO_NOT_SEND)
async def on_process_multiplication(message: Message, properties: dict[str, Any]):
    payload = json.loads(message.payload)
    return payload["a"] * payload["b"]


async def main():
    # fastmqtt = FastMQTT("test.mosquitto.org")
    # fastmqtt.include_router(router)
    # async with fastmqtt:
    # OR
    async with FastMQTT("test.mosquitto.org", routers=[router]) as fastmqtt:
        await fastmqtt.publish("test/fastmqtt/print_message", "Hello, world!")

        async with fastmqtt.response_context(
            f"test/fastmqtt/process/response/{fastmqtt.identifier}"
        ) as ctx:
            response = await ctx.request(
                "test/fastmqtt/process/substruction", json.dumps({"a": 10, "b": 5})
            )
            print(f"Substruction result: {response.payload.decode()}")

            response = await ctx.request(
                "test/fastmqtt/process/multiplication", json.dumps({"a": 20, "b": 30})
            )
            print(f"Multiplication result: {response.payload.decode()}")


if __name__ == "__main__":
    asyncio.run(main())
