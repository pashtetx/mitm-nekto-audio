from aiortc.mediastreams import AudioStreamTrack
from aiortc.contrib.media import MediaRecorder
from av import AudioFrame
import av
import asyncio

class AudioRedirect(AudioStreamTrack):
    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        super().__init__()

    async def recv(self) -> AudioFrame:
        frame = await self._queue.get()
        return frame

class MediaRedirect:
    def __init__(self, file: str) -> None:
        self.__audio = AudioRedirect()
        self.container = av.open(
            file=file, mode="w",
        )
        self.stream = self.container.add_stream(codec_name="mp3")
        self.track = None

    def add_track(self, track: AudioRedirect) -> None:
        self.track = track

    @property
    def audio(self) -> AudioRedirect:
        return self.__audio

    async def start(self) -> None:
        asyncio.ensure_future(self.__run_track(self.track))

    async def __run_track(self, track: AudioRedirect) -> None:
        while True:
            try:
                frame = await track.recv()
            except Exception as e:
                return
            for packet in self.stream.encode(frame):
                self.container.mux(packet)
            await self.__audio._queue.put(frame)
            
    