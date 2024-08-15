# import asyncio

# from fastmqtt import FastMqtt, Message, MqttRouter

# router = MqttRouter()


# @router.on_message("temperature/request")
# async def temp_request_handler(message: Message):
#     # Simulate getting a temperature reading
#     return 25  # Return the temperature


# async def main():
#     async with FastMqtt("test.mosquitto.org", routers=[router]) as fastmqtt:
#         ...
#         async with fastmqtt.response_context(f"temperature/response/{fastmqtt.identifier}") as ctx:
#             response = await ctx.request("temperature/request")
#             print(f"Temperature: {response.payload.text()}")


# if __name__ == "__main__":
#     asyncio.run(main())
