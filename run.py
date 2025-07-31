import asyncio
from core.client import Client
from core.room import Room

async def main() -> None:
    client = Client(
        user_id="9a80c82b-6d0b-44e4-ac36-a7f55c242416",
        ua="Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
    )
    room = Room()
    room.add_member(client)
    await client.connect()

asyncio.run(main())