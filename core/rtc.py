from aiortc.mediastreams import AudioStreamTrack
from av import AudioFrame

from core.discord.sink import RedirectFromDiscordStream

from discord import VoiceClient

from utils import mix_audio_frames

from datetime import datetime
from pathlib import Path
import av
import asyncio

class RedirectDiscord:
    def __init__(self, vc: VoiceClient) -> None:
        self._queues = dict()
        self.vc = vc
        self.container = av.open(
            file=Path("dialogs") /
            datetime.now().strftime("%Y-%m-%d-%H-%M-%S.mp3"), mode="w",
        )
        self.stream = self.container.add_stream(codec_name="mp3")

    async def recv(self) -> None:
        if len(self._queues) < 2:
            return
        if all([queue.qsize() > 1 for _, queue in self._queues.items()]):
            frames = []
            for _, queue in self._queues.items():
                frame = await queue.get()  
                frames.append(frame)               
            mixed = mix_audio_frames(*frames)
            for plane in mixed.planes:
                packet = bytes(plane)
                self.vc.send_audio_packet(packet)
            for packet in self.stream.encode(mixed):
                self.container.mux(packet)

class AudioRedirect(AudioStreamTrack):
    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        super().__init__()

    async def recv(self) -> AudioFrame:
        frame = await self._queue.get()
        return frame

class MediaRedirect:
    def __init__(
        self, 
    ) -> None:
        self.__audio = AudioRedirect()
        self.track = None
        self.stoped = False
        self.redirect_from_discord = None
        self.redirect_to_discord = None

    def set_redirect_from_discord(self, stream: RedirectFromDiscordStream) -> None:
        self.redirect_from_discord = stream

    def set_redirect_to_discord(self, redirect_to_discord: RedirectDiscord) -> None:
        self.redirect_to_discord = redirect_to_discord
        self.redirect_to_discord._queues.update({self.__audio:asyncio.Queue()}) 

    def add_track(self, track: AudioRedirect) -> None:
        self.track = track

    @property
    def audio(self) -> AudioRedirect:
        return self.__audio

    async def start(self) -> None:
        asyncio.ensure_future(self.__run_track(self.track))

    async def stop(self) -> None:
        self.stoped = True

    async def __run_track(self, track: AudioRedirect) -> None:
        while True:
            if self.stoped:
                break
            try:
                frame = await track.recv()
                discord_frame = None
                if self.redirect_from_discord:
                    discord_frame = self.redirect_from_discord.recv()
            except Exception as e: 
                return
            if self.redirect_to_discord:
                try:
                    await self.redirect_to_discord._queues[self.__audio].put(frame)
                    await self.redirect_to_discord.recv()
                except OSError as e:
                    print("pass")
            if discord_frame:
                frame = mix_audio_frames(frame, discord_frame)
            await self.__audio._queue.put(frame)
            
    