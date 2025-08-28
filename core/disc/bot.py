from core.room import Room
from config import parse_clients_config
from .sink import RedirectSink, RedirectFromDiscordStream
import discord

bot = discord.Bot(intents=discord.Intents.all())

@bot.event
async def on_ready() -> None:
    acitivity = discord.Game(
        name="Некто.ми",
        type=3
    )
    await bot.change_presence(activity=acitivity)

@bot.slash_command(name="start", guild_ids=[1270812703874879663])
async def start(ctx: discord.ApplicationContext):
    await ctx.respond("Connecting...")
    sink = RedirectSink()
    room = Room()
    voice = ctx.author.voice
    if not voice:
        return await ctx.respond("Not in voice!")
    voice = await voice.channel.connect()
    room.set_discord_redirect(voice)
    for client in parse_clients_config():
        stream = RedirectFromDiscordStream()
        sink.add_queue(stream.get_queue())
        room.add_member(client, bot, stream)
        if not client.transport.connected:
            await client.connect()
        else:
            await client.search()
    voice.start_recording(
        sink,
        print,
        ctx.channel
    )
    await ctx.respond("Started!")
