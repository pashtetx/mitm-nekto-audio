from core.room import Room, Member, Reconnect
from config import parse_clients_config, discord_config

from core.handlers.client import register_client_handlers
from core.handlers.peer import register_peer_handlers

from pathlib import Path
from core.rtc import MediaRedirect

import discord
import asyncio
import time

bot = discord.Bot(intents=discord.Intents.all())

room = Room()

@bot.event
async def on_ready() -> None:
    acitivity = discord.Game(
        name="Некто.ми",
        type=3
    )
    await bot.change_presence(activity=acitivity)

async def connect(channel: discord.TextChannel, author: discord.User) -> None:
    await channel.send("Connecting...")
    voice = author.voice
    if not voice:
        return await channel.send("Not in voice!")
    voice = voice.channel
    room.set_voice_client(voice)
    for client in parse_clients_config():
        room.add_member(Member(
                client=client,
                redirect=MediaRedirect(file="dialogs" / Path(f"{client.user_id}-{round(time.time())}.mp3"),)
            )
        )
        register_client_handlers(client)
        register_peer_handlers(client)
        if not client.connected:
            asyncio.ensure_future(client.connect(wait=True))
        else:
            await client.search()
    await channel.send("Started!")

@bot.event
async def on_message(message: discord.Message):
    if message.content == "$start":
        room.set_reconnect(Reconnect(connect, message.channel, message.author))
        await connect(message.channel, message.author)
    if message.content == "$stop":
        await room.stop()
    if message.content == "$next":
        await room.stop()
        await asyncio.sleep(discord_config.get("reconnect_delay"))
        await connect(message.channel, message.author)
