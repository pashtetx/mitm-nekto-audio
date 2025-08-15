import asyncio
from core.client import Client
from core.room import Room

from config import parse_clients_config

async def main() -> None:
    room = Room()
    tasks = list()
    for client in parse_clients_config():
        room.add_member(client)
        tasks.append(client.connect())
    await asyncio.gather(*tasks)
        
if __name__ == "__main__":
    asyncio.run(main())