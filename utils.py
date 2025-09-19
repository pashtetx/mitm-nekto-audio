import hashlib
import base64
import av
from typing import AsyncGenerator, List
import numpy as np
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer

def alarm(user_id: str, internal_id: int) -> str:
    payload = user_id + "BYdKPTYYGZ7ALwA" + "8oNm2" + str(internal_id)
    return base64.b64encode(
        hashlib.sha256(payload.encode())
        .hexdigest().encode()
    ).decode()

async def get_ice_candidates(pc: RTCPeerConnection) -> AsyncGenerator:
    for transceiver in pc.getTransceivers():
        iceGatherer = transceiver.sender.transport.transport.iceGatherer
        for candidate in iceGatherer.getLocalCandidates():
            yield candidate

def mix_audio_frames(frame1: av.AudioFrame, frame2: av.AudioFrame) -> av.AudioFrame:
    audio = frame1.to_ndarray()
    audio2 = frame2.to_ndarray()
    mixed = audio + audio2
    frame = av.AudioFrame.from_ndarray(mixed, format=frame1.format, layout=frame1.layout)
    frame.pts = max(frame1.pts, frame2.pts)
    frame.sample_rate = frame1.sample_rate
    frame.time_base = frame1.time_base
    return frame

def parse_turn_params(params: List[str]) -> RTCConfiguration:
    turn_params = list(filter(lambda key: not key["url"].startswith("turn:["), 
        params))
    return RTCConfiguration(
        iceServers=[RTCIceServer(
            urls=turn_param.get("url"),
            username=turn_param.get("username"),
            credential=turn_param.get("credential"),
        ) for turn_param in turn_params]
    )