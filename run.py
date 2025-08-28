from config import get_discord_token, parse_clients_config
from core.disc.bot import bot
from core.room import Room
import asyncio

def start() -> None:
    token = get_discord_token()
    if token:
        bot.run(token)
    else:
        room = Room()
        tasks = list()
        for client in parse_clients_config():
            room.add_member(client)
            tasks.append(client.connect())
        asyncio.run(asyncio.gather(*tasks))

if __name__ == "__main__":
    start()