from .client import Client
from typing import Dict, Any
from .transport import Transport

from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer

import json

class Room:
    def __init__(self) -> None:
        self.members = list()
        self.pcs = dict()
        self.connections = dict()
    
    def add_member(self, client: Client) -> None:
        client.add_action("offer", self.on_offer)
        client.add_action("peer-connect", self.on_peer)
        client.add_action("answer", self.on_answer)
        client.add_action("ice-candidate", self.on_ice_candidate)
        self.members.append(client)

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
            pass

        if initiator:
            pc.addTrack()
            offer = await pc.createOffer()


    async def on_offer(self, transport: Transport, payload: Dict[str, Any]) -> None:
        pass

    async def on_answer(self, transport: Transport, payload: Dict[str, Any]) -> None:
        pass

    async def on_ice_candidate(self, transport: Transport, payload: Dict[str, Any]) -> None:
        pass