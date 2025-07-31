from aiortc.contrib.media import PlayerStreamTrack
import asyncio

class MediaRedirect:

    def __init__(self) -> None:
        self.__audio = PlayerStreamTrack(self, kind="audio")

    def add_track(self, track: PlayerStreamTrack) -> None:
        self.track = track

    @property
    def audio(self) -> PlayerStreamTrack:
        return self.__audio

    async def start(self) -> None:
        asyncio.ensure_future(self.__run_track(self.track))

    async def __run_track(self, track: PlayerStreamTrack) -> None:
        while True:
            try:
                frame = await track.recv()
            except Exception as e:
                return
                print("EXCEPTION", e)
            await self.__audio._queue.put(frame)

    