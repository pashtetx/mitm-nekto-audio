from .client import Client
from typing import Dict, Any, List, Self, Optional, Callable, Awaitable, Union
from .rtc import MediaRedirect
from utils import get_ice_candidates
from aiortc import RTCPeerConnection
from aiortc.mediastreams import AudioStreamTrack

from aiortc.contrib.signaling import object_to_string

from dataclasses import dataclass
from utils import parse_turn_params

from core.discord.sink import RedirectSink, RedirectFromDiscordStream
from core.rtc import MediaRedirect, RedirectDiscord

from config import discord_config

from contextlib import suppress

import asyncio
import discord
import json

async def once_done(sink: discord.sinks, *args):
    await sink.vc.disconnect()

@dataclass
class Member:
    client: Client
    redirect: Optional[MediaRedirect] = None
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
        self.vc = None

    def set_voice_client(self, vc: discord.VoiceClient) -> None:
        self.vc = vc
        self.sink = RedirectSink()
        self.redirect_to_discord = None

    def set_reconnect(self, reconnect: Reconnect) -> None:
        self.reconnect_callback = reconnect

    async def connect_voice(self) -> None:
        if not self.vc:
            return
        voice = await self.vc.connect()
        redirect_to_discord = RedirectDiscord(voice)
        for member in self.members:
            stream = RedirectFromDiscordStream()
            self.sink.add_queue(stream.get_queue())
            member.redirect.set_redirect_to_discord(redirect_to_discord)
            member.redirect.set_redirect_from_discord(stream)
        voice.start_recording(
            self.sink,
            once_done,
            self.vc,
        )

    def add_member(self, member: Member) -> None:
        member.client.add_action("peer-connect", self.__on_peer)
        member.client.add_action("peer-disconnect", self.__on_close)
        member.client.add_action("search.out", self.__on_close)
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

    async def disconnect_all_members(self) -> None:
        for member in self.members:
            with suppress(AttributeError):
                if member.client.get_connection_id():
                    await member.client.peer_disconnect()

    async def disconnect_voice(self, redirect: MediaRedirect) -> None:
        voice = redirect.redirect_to_discord
        if not voice:
            return
        voice = voice.vc
        if not voice or not voice.is_connected():
            return
        await voice.disconnect(force=True)

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

    def __on_peer(self, client: Client, payload: Dict[str, Any], *args, **kwargs) -> None:
        member = self.get_member_by_client(client)
        if not member:
            return
        configuration = parse_turn_params(json.loads(payload.get("turnParams")))
        pc = RTCPeerConnection(configuration=configuration)
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
        await self.disconnect_all_members()
        await client.disconnect()
        await redirect.stop()
        client.dispatcher.clear_default()
        client.dispatcher.clear_action()
        self.members.remove(self.get_member_by_client(client))
        await self.disconnect_voice(redirect)
        if len(self.members) == 1:
            await self.__reconnect()

    async def stop(self) -> None:
        for member in self.members:
            client = member.client
            redirect = member.redirect
            pc = member.pc
            if pc and pc.connectionState == "connected":
                await pc.close()
            await redirect.stop()
            await self.disconnect_voice(member.redirect)
            await client.peer_disconnect()                    
            await client.disconnect()
            client.dispatcher.clear_default()
            client.dispatcher.clear_action()
        self.members.clear()
        await self.__reconnect()