from config import discord_config, parse_clients_config
from core.disc.bot import bot
from core.room import Room

from pathlib import Path

from log import log

import asyncio
import os

def start() -> None:
    log.info("Created by r8du...")
    if not os.path.exists(Path("dialogs")):
        os.mkdir("dialogs")
    token = discord_config.get("token")
    if token:
        log.info("Send $start in discord channel!")
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