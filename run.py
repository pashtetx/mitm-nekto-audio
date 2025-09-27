from config import parse_clients_config, load_discord
from core.discord.bot import bot
from core.rtc import MediaRedirect, MediaRecorder
from core.room import Room, Member
from core.handlers import register_client_handlers, register_peer_handlers

from pathlib import Path

from log import log

import asyncio
import os

async def start_without_bot() -> None:
    room = Room()
    tasks = list()
    recorder = MediaRecorder()
    for client in parse_clients_config():
        room.add_member(
            Member(
                client=client,
                redirect=MediaRedirect(recorder=recorder)
            )
        )
        register_client_handlers(client)
        register_peer_handlers(client)
        tasks.append(client.connect(wait=True))
    await asyncio.gather(*tasks)

def start() -> None:
    log.info("Created by r8du...")
    if not os.path.exists(Path("dialogs")):
        os.mkdir("dialogs")
    token = load_discord("token")
    if token:
        log.info("Send $start in discord channel!")
        bot.run(token)
    else:
        asyncio.run(start_without_bot())

if __name__ == "__main__":
    start()