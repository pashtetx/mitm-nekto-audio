from .client import Client
from typing import Dict, Any
from .transport import Transport
from .rtc import MediaRedirect
from utils import get_ice_candidates
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription

from aiortc.contrib.signaling import object_to_string, candidate_from_sdp

import json

class Room:
    def __init__(self) -> None:
        self.members = list()
        self.pcs = dict()
        self.connections = dict()
        self.media_redirect = dict()
    
    def add_member(self, client: Client) -> None:
        client.add_action("offer", self.on_offer)
        client.add_action("peer-connect", self.on_peer)
        client.add_action("answer", self.on_answer)
        client.add_action("ice-candidate", self.on_ice_candidate)
        client.add_action("peer-disconnected", self.on_close)
        self.members.append(client.transport)

    async def send_ice_candidates(self, pc: RTCPeerConnection, transport: Transport) -> None:
        async for candidate in get_ice_candidates(pc):
            candidate_string = object_to_string(candidate)
            payload = {
                "type":"ice-candidate",
                "candidate":json.dumps({"candidate":candidate_string}),
                "connectionId":self.connections[transport],
            }
            await transport.emit("event", data=payload)

    async def on_peer(self, transport: Transport, payload: Dict[str, Any]) -> None:
        connection_id = payload.get("connectionId")
        initiator = payload.get("initiator")
        turn_params = list(filter(
            lambda item: not item["url"].startswith("turn["),
            json.loads(payload.get("turnParams"))
        ))
        pc = RTCPeerConnection(configuration=RTCConfiguration(
            iceServers=[RTCIceServer(
                urls=turn_param.get("url"),
                username=turn_param.get("username"),
                credential=turn_param.get("credential"),
            ) for turn_param in turn_params]
        ))
        self.pcs[transport] = pc
        self.connections[transport] = connection_id

        @pc.on("connectionstatechange")
        async def on_connection_state_chnage() -> None:
            if pc.connectionState == "failed":
                await pc.close()
            if pc.connectionState == "connected":
                payload = {
                    "type":"peer-connection",
                    "connectionId":connection_id,
                    "connected":True,
                }
                await transport.emit("event", data=payload)

        @pc.on("track")
        async def on_track(track) -> None:
            self.media_redirect[transport].add_track(track)
            payload = {
                "type":"stream-received",
                "connectionId":self.connections[transport]
            }
            await transport.emit("event", data=payload)

        if initiator:
            media_redirect = MediaRedirect()
            pc.addTrack(media_redirect.audio)
            self.media_redirect[transport] = media_redirect
            offer = await pc.createOffer()
            pc.setLocalDescription(offer)
            payload = {
                "type":"offer",
                "offer":json.dumps({"sdp":offer.sdp, "type": offer.type}),
                "connectionId":self.connections[transport],
            }
            await transport.emit("event", data=payload)

    async def on_offer(self, transport: Transport, payload: Dict[str, Any]) -> None:
        pc = self.pcs.get(transport)
        offer = json.loads(payload.get("offer"))
        remote_description = RTCSessionDescription(
            sdp=offer.get("sdp"),
            type=offer.get("type")
        )
        await pc.setRemoteDescription(remote_description)

        media_redirect = MediaRedirect()
        pc.addTrack(media_redirect.audio)
        self.media_redirect[transport] = media_redirect
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        payload = {
            "type":"answer",
            "answer": json.dumps({"sdp":answer.sdp, "type": answer.type}),
            "connectionId":self.connections[transport],
        }
        await transport.emit("event", data=payload)
        await self.send_ice_candidates(pc, transport)

    async def on_answer(self, transport: Transport, payload: Dict[str, Any]) -> None:
        pc = self.pcs.get(transport)
        answer = json.loads(payload.get("answer"))
        remote_description = RTCSessionDescription(
            sdp=answer.get("sdp"),
            type=answer.get("type")
        )
        await pc.setRemoteDescription(remote_description)
        await self.send_ice_candidates(pc, transport)

    async def on_ice_candidate(self, transport: Transport, payload: Dict[str, Any]) -> None:
        pc = self.pcs.get(transport)
        candidate = candidate_from_sdp(
            json.loads(payload.get("candidate")).get("candidate").get("candidate")
        )
        await pc.addIceCandidate(candidate)

    async def on_close(self, transport: Transport, payload: Dict[str, Any]) -> None:
        pc = self.pcs.get(transport)
        await pc.close()
