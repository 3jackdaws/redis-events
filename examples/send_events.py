from redis_events import Client, Event

client = Client()


async def send_events():
    event = Event("message", {"test":1})
    await client.send(event)
    print("send event")
    reply = await client.wait_for_reply(event)
    print('got reply')
    event = Event("control", {"Hello":"world!"})
    await client.send(event)




import asyncio

asyncio.get_event_loop().run_until_complete(send_events())