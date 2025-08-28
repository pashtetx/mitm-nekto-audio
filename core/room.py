from .client import Client
from typing import Dict, Any
from .transport import Transport
from .rtc import MediaRedirect, RedirectDiscord
from utils import get_ice_candidates
from aiortc import RTCPeerConnection, RTCConfiguration, RTCIceServer, RTCSessionDescription

from aiortc.contrib.signaling import object_to_string, candidate_from_sdp
from pathlib import Path

from discord.voice_client import VoiceClient
from discord import Bot

from core.disc.sink import RedirectFromDiscordStream

import os
import json

class Room:

    @staticmethod
    def clear_client(client: Client) -> None:
        client.remove_action("offer")
        client.remove_action("peer-connect")
        client.remove_action("answer")
        client.remove_action("ice-candidate")
        client.remove_action("peer-disconnect")

    def __init__(self) -> None:
        self.clients = list()
        self.pcs = dict()
        self.connections = dict()
        self.media_redirect = dict()
        self.loggers = dict()
        self.bots = dict()
        self.discord_redirect = None
        self.create_dialogs_dir()

    def set_discord_redirect(self, vc: VoiceClient) -> None:
        self.discord_redirect = RedirectDiscord(vc)

    def clear(self) -> None:
        self.pcs.clear()
        self.connections.clear()
        self.media_redirect.clear()
        self.bots.clear()
        self.clients.clear()

    @staticmethod
    def create_dialogs_dir() -> None:
        if not os.path.exists(Path("dialogs")):
            os.mkdir("dialogs")

    def add_member(self, client: Client, bot: Bot = None, stream: RedirectFromDiscordStream = None) -> None:
        self.clients.append(client)
        client.add_action("offer", self.on_offer)
        client.add_action("peer-connect", self.on_peer)
        client.add_action("answer", self.on_answer)
        client.add_action("ice-candidate", self.on_ice_candidate)
        client.add_action("peer-disconnect", self.on_close)
        self.loggers[client.transport] = client.client_logger
        self.media_redirect[client.transport] = MediaRedirect(
            file="dialogs" / Path(f"{client.user_id}.mp3"),
            redirect_to_discord=self.discord_redirect,
            redirect_from_discord=stream,
        )
        self.bots[client.transport] = bot

    async def send_ice_candidates(self, pc: RTCPeerConnection, transport: Transport) -> None:
        log = self.get_client_logger(transport)
        log.info("Sending ice canidates.") 
        async for candidate in get_ice_candidates(pc):
            candidate_string = json.loads(object_to_string(candidate)).get("candidate")
            payload = {
                "type":"ice-candidate",
                "candidate":json.dumps(
                    {
                        "candidate":{
                            "candidate":candidate_string,
                            "sdpMid":0, 
                            "sdpMLineIndex":0
                        }, 
                    }
                ),
                "connectionId":self.connections[transport],
            }
            await transport.emit("event", data=payload)
            log = self.get_client_logger(transport)
            log.info("Sent ice canidates.") 

    def get_client_logger(self, transport: Transport) -> None:
        return self.loggers[transport]

    async def on_peer(self, transport: Transport, payload: Dict[str, Any]) -> None:
        log = self.get_client_logger(transport)
        connection_id = payload.get("connectionId")
        initiator = payload.get("initiator")
        log.info("The user found the partner", initiator=initiator, connection_id=connection_id)
        turn_params = list(filter(
            lambda item: not item["url"].startswith("turn:["),
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
        async def on_connection_state_change() -> None:
            if pc.connectionState == "connecting":
                log.info("Connection state change to *connecting*.")
            if pc.connectionState == "failed":
                log.info("Connection state change to *failed*.")
                await pc.close()
            if pc.connectionState == "connected":
                payload = {
                    "type":"peer-connection",
                    "connectionId":connection_id,
                    "connection":True,
                }
                log.info("Connection state change to *connected*")
                await transport.emit("event", data=payload)

        @pc.on("track")
        async def on_track(track) -> None:
            for transport_key, media_redirect in self.media_redirect.items():
                if transport_key != transport:
                    self.media_redirect[transport_key].add_track(track)
            if all([redirect.track for _, redirect in self.media_redirect.items()]):
                for _, redirect in self.media_redirect.items():
                    await redirect.start()
            log.info("User received a track.")
            payload = {
                "type":"stream-received",
                "connectionId":self.connections[transport]
            }
            await transport.emit("event", data=payload)

        if initiator:
            media_redirect = self.media_redirect[transport]
            pc.addTrack(media_redirect.audio)
            offer = await pc.createOffer()
            await pc.setLocalDescription(offer)
            payload = {
                "type":"peer-mute",
                "connectionId":self.connections[transport],
                "muted":False
            }
            await transport.emit("event", data=payload)
            payload = {
                "type":"offer",
                "offer":json.dumps({"sdp":offer.sdp, "type": offer.type}),
                "connectionId":self.connections[transport],
            }
            await transport.emit("event", data=payload)

    async def on_offer(self, transport: Transport, payload: Dict[str, Any]) -> None:
        log = self.get_client_logger(transport)
        log.info("Received offer.")
        pc = self.pcs.get(transport)
        offer = json.loads(payload.get("offer"))
        remote_description = RTCSessionDescription(
            sdp=offer.get("sdp"),
            type=offer.get("type")
        )
        await pc.setRemoteDescription(remote_description)

        media_redirect = self.media_redirect[transport]
        pc.addTrack(media_redirect.audio)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        payload = {
            "type":"answer",
            "answer": json.dumps({"sdp":answer.sdp, "type": answer.type}),
            "connectionId":self.connections[transport],
        }
        log.info("Sent answer.")
        await transport.emit("event", data=payload)
        await self.send_ice_candidates(pc, transport)

    async def on_answer(self, transport: Transport, payload: Dict[str, Any]) -> None:
        log = self.get_client_logger(transport)
        log.info("Received answer.") 
        pc = self.pcs.get(transport)
        answer = json.loads(payload.get("answer"))
        remote_description = RTCSessionDescription(
            sdp=answer.get("sdp"),
            type=answer.get("type")
        )
        await pc.setRemoteDescription(remote_description)
        await self.send_ice_candidates(pc, transport)

    async def on_ice_candidate(self, transport: Transport, payload: Dict[str, Any]) -> None:
        log = self.get_client_logger(transport)
        log.info("Received ice candidate")
        pc = self.pcs.get(transport)
        candidate_payload = json.loads(payload.get("candidate")).get("candidate")
        candidate = candidate_from_sdp(
            candidate_payload.get("candidate")
        )
        candidate.sdpMid = candidate_payload.get("sdpMid")
        candidate.sdpMLineIndex = candidate_payload.get("sdpMLineIndex")
        await pc.addIceCandidate(candidate)

    async def on_close(self, transport: Transport, payload: Dict[str, Any]) -> None:
        log = self.get_client_logger(transport)
        log.info("Partner disconnected.")
        pc = self.pcs.get(transport)
        await pc.close()
        for client in self.clients:
            if client.transport != transport:
                if self.connections.get(client.transport):
                    await client.peer_disconnect(self.connections[client.transport])
            else:
                self.clear_client(client)
        media_redirect = self.media_redirect.get(transport)
        if media_redirect:
            voice = media_redirect.redirect_to_discord.vc
            if voice.is_connected():
                await voice.disconnect(force=True) 
        if all([pc.connectionState == "closed" for _, pc in self.pcs.items()]):
            log.info("Clear room.")
            self.clear()
            
