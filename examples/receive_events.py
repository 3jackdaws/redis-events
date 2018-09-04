from redis_events import Client, Event


client = Client()


@client.event("message")
async def on_message(event:Event):
    print("GOT EVENT")
    print(event)
    reply_event = Event("other", {"hello":"world"})
    print('SENDING REPLY')
    await client.send_reply(event, reply_event)


@client.event("control")
async def on_control(event:Event):
    print(f"CONTROL: {event.data}")



client.run()