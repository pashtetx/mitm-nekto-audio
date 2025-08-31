from .client import Client
from typing import Dict, Any, List, Self, Optional, Callable, Awaitable, Union
from .rtc import MediaRedirect
from utils import get_ice_candidates
from aiortc import RTCPeerConnection
from aiortc.mediastreams import AudioStreamTrack

from aiortc.contrib.signaling import object_to_string

from dataclasses import dataclass
from utils import parse_turn_params

from config import discord_config

import asyncio
import discord
import json

@dataclass
class Member:
    client: Client
    redirect: MediaRedirect
    pc: Optional[RTCPeerConnection] = None

@dataclass
class Reconnect:
    callback: Union[Awaitable, Callable]
    channel: discord.TextChannel
    user: discord.User

class Room:

    def __init__(self) -> None:
        self.members: List[Member] = list()
        self.reconnect_callback = None
    
    def set_reconnect(self, reconnect: Reconnect) -> None:
        self.reconnect_callback = reconnect

    def add_member(self, member: Member) -> None:
        member.client.add_action("peer-connect", self.__on_peer)
        member.client.add_action("peer-disconnect", self.__on_close)
        self.members.append(member)
    
    def get_member_by_client(self, client: Client) -> Member:
        for member in self.members:
            if member.client == client:
                return member

    def add_members_track(self, track: AudioStreamTrack, client: Client) -> None:
        for member in self.members:
            if member.client == client:
                continue
            member.redirect.add_track(track)

    async def __reconnect(self) -> None:
        if discord_config.get("reconnect") and self.reconnect_callback:
            await asyncio.sleep(discord_config.get("reconnect_delay"))
            await self.reconnect_callback.callback(
                self.reconnect_callback.channel,
                self.reconnect_callback.user
            )

    async def send_ice_candidates(self, pc: RTCPeerConnection, client: Client) -> None:
        log = client.log
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
                "connectionId":client.get_connection_id(),
            }
            await client.emit("event", data=payload)
            log.info("Sent ice canidates.") 

    def __on_peer(self, client: Client, payload: Dict[str, Any]) -> None:
        configuration = parse_turn_params(json.loads(payload.get("turnParams")))
        pc = RTCPeerConnection(configuration=configuration)
        member = self.get_member_by_client(client)
        member.pc = pc
        client.dispatcher.default_update({
            "pc":pc,
            "redirect":member.redirect,
            "room":self,
        })

    async def __on_close(self,
        client: Client, 
        payload: Dict[str, Any],
        redirect: MediaRedirect,
        pc: RTCPeerConnection,
        room: Self,
    ) -> None:
        for member in self.members:
            if member.client != client:
                await member.client.peer_disconnect()
        member = self.get_member_by_client(client)
        if not member:
            return
        client = member.client
        redirect = member.redirect
        pc = member.pc
        await pc.close()
        await client.disconnect()
        await redirect.stop()
        client.dispatcher.clear_action()
        await client.disconnect()
        self.members.remove(member)
        client.dispatcher.default_remove("redirect")
        client.dispatcher.default_remove("room")
        client.dispatcher.default_remove("pc")
        voice = redirect.redirect_to_discord.vc
        if voice.is_connected():
            await voice.voice_disconnect()
            await voice.disconnect(force=True)
        if not voice.is_connected():
            await self.__reconnect()    

    async def stop(self) -> None:
        for member in self.members.copy():
            client = member.client
            redirect = member.redirect
            pc = member.pc
            await client.peer_disconnect()
            await pc.close()
            await redirect.stop()
            voice = redirect.redirect_to_discord.vc
            if voice.is_connected():
                await voice.disconnect()
            client.dispatcher.clear_action()
            await client.disconnect()
            self.members.clear()
            client.dispatcher.default_remove("redirect")
            client.dispatcher.default_remove("room")
            client.dispatcher.default_remove("pc")