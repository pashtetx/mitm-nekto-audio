from aiortc.mediastreams import AudioStreamTrack
from av import AudioFrame

from core.discord.sink import RedirectFromDiscordStream

from discord import VoiceClient

from utils import mix_audio_frames

from contextlib import suppress

from datetime import datetime
from pathlib import Path
import av
import asyncio

class BaseMedia:

    def __init__(self):
        self._queues = dict()

    async def callback(self, mixed: av.AudioFrame) -> None:
        raise NotImplementedError()

    async def recv(self) -> None:
        if len(self._queues) < 2:
            return
        if all([queue.qsize() > 1 for _, queue in self._queues.items()]):
            frames = []
            for _, queue in self._queues.items():
                frame = await queue.get()  
                frames.append(frame)               
            mixed = mix_audio_frames(*frames)
            await self.callback(mixed)

    async def put(self, frame: av.AudioFrame, track: AudioStreamTrack) -> None:
        if not self._queues.get(track):
            self._queues.update({track:asyncio.Queue()})
        await self._queues[track].put(frame) 
        await self.recv()

class MediaRecorder(BaseMedia):
    def __init__(self, file: str = None):
        file = file or Path("dialogs") / datetime.now().strftime("%Y-%m-%d-%H-%M-%S.mp3")
        self.container = av.open(
            file=file, mode="w",
        )
        self.stream = self.container.add_stream(codec_name="mp3")
        super().__init__()

    async def callback(self, mixed):
        for packet in self.stream.encode(mixed):
            self.container.mux(packet)

class RedirectDiscord(BaseMedia):
    def __init__(self, vc: VoiceClient) -> None:
        self.vc = vc
        super().__init__()

    async def callback(self, mixed):
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
        recorder: MediaRecorder,
    ) -> None:
        self.__audio = AudioRedirect()
        self.track = None
        self.started = False
        self.redirect_from_discord = None
        self.redirect_to_discord = None
        self.task = None
        self.recorder = recorder
        self.muted = False

    def set_redirect_from_discord(self, stream: RedirectFromDiscordStream) -> None:
        self.redirect_from_discord = stream

    def set_redirect_to_discord(self, redirect_to_discord: RedirectDiscord) -> None:
        self.redirect_to_discord = redirect_to_discord

    def add_track(self, track: AudioRedirect) -> None:
        self.track = track

    def mute(self) -> None:
        self.muted = True

    def unmute(self) -> None:
        self.muted = False

    @property
    def audio(self) -> AudioRedirect:
        return self.__audio

    async def start(self) -> None:
        self.started = True
        self.task = asyncio.ensure_future(self.__run_track(self.track))

    async def stop(self) -> None:
        self.started = False
        if self.task:
            print("CANCEL")
            self.task.cancel()

    async def __run_track(self, track: AudioRedirect) -> None:
        while True:
            if self.muted:
                continue
            try:
                frame = await track.recv()
                discord_frame = None
                if self.redirect_from_discord:
                    discord_frame = self.redirect_from_discord.recv()
                await self.recorder.put(frame, self.__audio)
            except Exception as e:
                # print(e)  
                return
            if self.redirect_to_discord:
                with suppress(OSError):
                    await self.redirect_to_discord.put(frame, self.__audio)
            if discord_frame:
                frame = mix_audio_frames(frame, discord_frame)
            await self.__audio._queue.put(frame)
            
    