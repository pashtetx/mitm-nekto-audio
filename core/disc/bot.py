from core.room import Room, Member, Reconnect
from config import parse_clients_config, discord_config
from .sink import RedirectSink, RedirectFromDiscordStream

from core.rtc import MediaRedirect, RedirectDiscord
from core.handlers.client import register_client_handlers
from core.handlers.peer import register_peer_handlers
from pathlib import Path

import discord
import asyncio

bot = discord.Bot(intents=discord.Intents.all())

room = Room()

@bot.event
async def on_ready() -> None:
    acitivity = discord.Game(
        name="Некто.ми",
        type=3
    )
    await bot.change_presence(activity=acitivity)

async def once_done(sink: discord.sinks, channel: discord.TextChannel, *args):
    await sink.vc.disconnect()
    await channel.send("End!")

async def connect(channel: discord.TextChannel, author: discord.User) -> None:
    await channel.send("Connecting...")
    sink = RedirectSink()
    voice = author.voice
    if not voice:
        return await channel.send("Not in voice!")
    voice = await voice.channel.connect()
    redirect_to_discord = RedirectDiscord(voice)
    for client in parse_clients_config():
        stream = RedirectFromDiscordStream()
        sink.add_queue(stream.get_queue())
        redirect = MediaRedirect(
            file="dialogs" / Path(f"{client.user_id}.mp3"),
            redirect_from_discord=stream,
            redirect_to_discord=redirect_to_discord
        )
        room.add_member(Member(client=client, redirect=redirect))
        register_client_handlers(client)
        register_peer_handlers(client)
        if not client.connected:
            asyncio.ensure_future(client.connect(wait=True))
        else:
            await client.search()
    voice.start_recording(
        sink,
        once_done,
        channel
    )
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
