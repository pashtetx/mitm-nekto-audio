from discord.sinks.core import Sink
from aiortc.codecs.opus import SAMPLES_PER_FRAME, SAMPLE_RATE
from aiortc.mediastreams import AudioStreamTrack
from typing import Optional
import av
import asyncio

class RedirectSink(Sink):

    def __init__(self, filters=None):
        self._queues = list()
        super().__init__(filters=filters)

    def add_queue(self, queue: asyncio.Queue) -> None:
        self._queues.append(queue)

    def write(self, data, user):
        frame = av.AudioFrame(samples=SAMPLES_PER_FRAME)
        plane = frame.planes[0]
        if len(data) == 3840:
            frame.pts = 0
            frame.sample_rate = SAMPLE_RATE
            plane.update(data)
            for queue in self._queues:
                queue.put_nowait(frame)  
        else:
            data = data[:int(len(data) / 3840)]
            for i in range(int(len(data) / 3840)):
                frame.planes[i].update(data[3840*i:i*3840+3840])

class RedirectFromDiscordStream(AudioStreamTrack):
    def __init__(self):
        self._queue = asyncio.Queue()
        super().__init__()

    def get_queue(self) -> asyncio.Queue:
        return self._queue

    def recv(self) -> Optional[av.AudioFrame]:
        try:
            return self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None