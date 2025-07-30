import hashlib
import base64

from aiortc import RTCPeerConnection

def alarm(user_id: str, internal_id: int) -> str:
    payload = user_id + "BYdKPTYYGZ7ALwA" + "8oNm2" + str(internal_id)
    return base64.b64encode(
        hashlib.sha256(payload.encode())
        .hexdigest().encode()
    ).decode()

async def get_ice_candidates(pc: RTCPeerConnection) -> None:
    for transceiver in pc.getTransceivers():
        iceGatherer = transceiver.sender.transport.transport.iceGatherer
        for candidate in iceGatherer.getLocalCandidates():
            yield candidate
