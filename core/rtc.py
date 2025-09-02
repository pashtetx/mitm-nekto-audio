from aiortc.mediastreams import AudioStreamTrack
from av import AudioFrame

from core.disc.sink import RedirectFromDiscordStream

from discord import VoiceClient

from utils import mix_audio_frames

import av
import asyncio

class RedirectDiscord:
    def __init__(self, vc: VoiceClient) -> None:
        self._queues = dict()
        self.vc = vc

    async def recv(self) -> None:
        if len(self._queues) < 2:
            return
        if all([queue.qsize() > 1 for _, queue in self._queues.items()]):
            frames = []
            max_pts = 0
            for _, queue in self._queues.items():
                frame = await queue.get()  
                frames.append(frame)               
            mixed = mix_audio_frames(*frames)
            for plane in mixed.planes:
                packet = bytes(plane)
            self.vc.send_audio_packet(packet)

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
        file: str, 
        redirect_to_discord: RedirectDiscord = None,
        redirect_from_discord: RedirectFromDiscordStream = None,
    ) -> None:
        self.__audio = AudioRedirect()
        self.container = av.open(
            file=file, mode="w",
        )
        self.redirect_to_discord = redirect_to_discord
        self.redirect_to_discord._queues.update({self.__audio:asyncio.Queue()}) 
        self.redirect_from_discord = redirect_from_discord
        self.stream = self.container.add_stream(codec_name="mp3")
        self.track = None
        self.stoped = False

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
            for packet in self.stream.encode(frame):
                self.container.mux(packet)
            await self.__audio._queue.put(frame)
            
    