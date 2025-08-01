from aiortc.mediastreams import AudioStreamTrack
from av import AudioFrame
import asyncio

class AudioRedirect(AudioStreamTrack):

    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        super().__init__()

    async def recv(self) -> AudioFrame:
        frame = await self._queue.get()
        return frame

class MediaRedirect:

    def __init__(self) -> None:
        self.__audio = AudioRedirect()

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
                print("EXCEPTION", e)
            await self.__audio._queue.put(frame)

    