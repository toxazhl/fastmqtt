import asyncio

from fastmqtt import FastMqtt, Message, MqttRouter
from fastmqtt.encoders import JsonDecoder, JsonEncoder

router = MqttRouter()


@router.on_message("temperature/request")
async def temp_request_handler(message: Message):
    # Simulate getting a temperature reading
    print(message.payload.decode())
    region = message.payload.decode()["region"]
    return {"temperature": 25.0, "region": region}


async def main():
    async with FastMqtt(
        "test.mosquitto.org",
        routers=[router],
        payload_encoder=JsonEncoder(),
        payload_decoder=JsonDecoder(),
    ) as fastmqtt:
        ...
        async with fastmqtt.response_context(f"temperature/response/{fastmqtt.client_id}") as ctx:
            response = await ctx.request("temperature/request", {"region": "eu"})

            print(f"Temperature: {response.payload.decode()}")


if __name__ == "__main__":
    asyncio.run(main())
