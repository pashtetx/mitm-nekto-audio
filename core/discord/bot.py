from core.room import Room, Member
from config import (
    parse_clients_config, 
    load_discord,
    bool_load_discord, 
    load_safe_discord
)
from core.handlers.client import register_client_handlers
from core.handlers.peer import register_peer_handlers

from core.rtc import MediaRedirect, MediaRecorder

import asyncio
import discord

bot = discord.Bot(intents=discord.Intents.all())

room = Room(bot)

main_loop = None
stop_command = load_safe_discord("stop-command") or "$stop"
start_command = load_safe_discord("start-command") or "$start"

@bot.event
async def on_ready() -> None:
    acitivity = discord.Game(
        name="Некто.ми",
        type=3
    )
    await bot.change_presence(activity=acitivity)

async def connect(author: discord.User) -> None:
    try:
        while True:
            channel = await bot.fetch_channel(int(load_discord("channel-id")))
            text = (
                "● **Подключение к nekto.me...**\n"
                f"_Чтобы остановить  - `{stop_command}`_"
            )
            await channel.send(text)
            voice = author.voice
            if not voice:
                return await channel.send("Not in voice!")
            voice = voice.channel
            recorder = MediaRecorder()
            room.set_voice_client(voice)
            tasks = list()
            for client in parse_clients_config():
                register_client_handlers(client)
                room.add_member(
                    Member(
                        client=client,
                        redirect=MediaRedirect(recorder=recorder)
                    )
                )
                register_peer_handlers(client)
                tasks.append(client.connect(wait=True))
            await asyncio.gather(*tasks)
            if not bool_load_discord("reconnect"):
                break
            delay = int(load_discord("reconnect-delay"))
            await channel.send(f"● **Переподключаюсь через {delay} секунд...**")
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        raise

@bot.event
async def on_message(message: discord.Message):
    global main_loop
    if message.channel.id != int(load_discord("channel-id")) or \
            message.channel.guild.id != int(load_discord("guild-id")):
        return
    if message.content == start_command:
        if len(room.members) > 0:
            return await message.reply("● **Бот уже работает!**")
        main_loop = asyncio.ensure_future(connect(message.author))
    if message.content == stop_command:
        if len(room.members) > 0:
            await room.stop()
            main_loop.cancel()
            await message.reply("● **Стоп!**")
        else:
            await message.reply("● **Бот не запущен!**")
