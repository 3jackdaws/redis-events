import aioredis
import asyncio
import marshal
import os
from async_timeout import timeout as async_timeout


loop = asyncio.get_event_loop()





def get_random_id():
    length = 20
    lower_bound = 33
    upper_bound = 126
    diff = upper_bound - lower_bound
    id = bytearray(os.urandom(length))
    for i,c in enumerate(id):
        id[i] = (c % diff) + lower_bound
    return id.decode()


class Event:
    __slots__ = [
        "type",
        "data",
        "id",
    ]
    def __init__(self, type, data, *, id=None):
        self.type = type
        self.data = data
        if not id:
            id = get_random_id()
        self.id = id


    def serialize(self):
        return marshal.dumps({
            "id": self.id,
            "type": self.type,
            "data": self.data
        })

    @staticmethod
    def deserialize(bytes):
        event_dict = marshal.loads(bytes)

        type = event_dict.get('type')
        data = event_dict.get('data')
        id = event_dict.get('id')
        if type:
            return Event(type, data, id=id)
        raise Exception("Not an event")

    def __repr__(self):
        return f"Event(type={self.type}, data={self.data})"



class Client:
    _events = {}
    def __init__(self, host="localhost", port=6379, password=None, db=0):
        options = {
            'address'   : f'redis://{host}:{port}',
            'password'  : password,
            'db'        : db
        }
        self.redis = None  # type: aioredis.Redis
        loop.run_until_complete(self.__async_init(options))


    async def __async_init(self, options):
        self.rsend = await aioredis.create_redis(**options)
        self.rrecv = await aioredis.create_redis(**options)

    async def __send(self, key, event:Event):
        await self.rsend.rpush(key, event.serialize())

    async def __recv(self, *keys, timeout=0):
        key, raw_msg = await self.rrecv.blpop(*keys, timeout=timeout)
        return Event.deserialize(raw_msg)

    async def wait_for_event(self, timeout=0):
        return await self.__recv(*self._events.keys(), timeout=timeout)

    async def dispatch_event(self, event:Event):
        if event.type in self._events:
            for handler in self._events[event.type]:
                loop.create_task(handler(event))

    async def send(self, event: Event):
        await self.__send(event.type, event)

    async def wait_for_reply(self, to: Event, *, timeout=0):
        return await self.__recv(to.id, timeout=timeout)

    async def send_reply(self, to:Event, reply:Event):
        await self.__send(to.id, reply)

    def event(self, type: str):
        if not type in self._events:
            self._events[type] = []
        def register(handler):
            if asyncio.iscoroutine(handler):
                raise ValueError("Handler must be a coroutine.")
            self._events[type].append(handler)
        return register

    # Run this to wait for and dispatch events
    async def listen_for_events(self):
        while 1:
            event = await self.wait_for_event()
            await self.dispatch_event(event)

    def run(self):
        loop.run_until_complete(self.listen_for_events())

