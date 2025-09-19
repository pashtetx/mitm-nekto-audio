from core.room import Room, Member, Reconnect
from config import parse_clients_config

from core.handlers.client import register_client_handlers
from core.handlers.peer import register_peer_handlers

from core.rtc import MediaRedirect, MediaRecorder

import discord

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
    recorder = MediaRecorder()
    room.set_voice_client(voice)
    for client in parse_clients_config():
        register_client_handlers(client)
        room.add_member(
            Member(
                client=client,
                redirect=MediaRedirect(recorder=recorder)
            )
        )
        register_peer_handlers(client)
        await client.connect(wait=False)
    await channel.send("Started!")

@bot.event
async def on_message(message: discord.Message):
    if message.content == "$start":
        if len(room.members) > 0:
            return await message.reply("Already started!")
        await connect(message.channel, message.author)
    if message.content == "$stop":
        await room.stop()
