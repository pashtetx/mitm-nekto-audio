from core.client import Client
from core.rtc import MediaRedirect
from core.room import Room
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole
from aiortc.contrib.signaling import candidate_from_sdp
from contextlib import suppress
from typing import Dict, Any

import json

black_hole = MediaBlackhole()

async def on_peer(
    client: Client, 
    payload: Dict[str, Any],
    redirect: MediaRedirect,
    pc: RTCPeerConnection,
    room: Room,
) -> None:
    log = client.log
    initiator = payload.get("initiator")
    with suppress(AttributeError):
        for member in room.members:
            if member.client.get_connection_id() != client.get_connection_id():
                break
        else:
            return await room.stop()

    @pc.on("connectionstatechange")
    async def on_connection_state_change() -> None:
        if pc.connectionState == "connecting":
            log.info("Connection state change to *connecting*.")
        if pc.connectionState == "failed":
            log.info("Connection state change to *failed*.")
            await pc.close()
            await room.stop()
        if pc.connectionState == "closed":
            log.info("Connection state change to *closed*.")
            await pc.close()
        if pc.connectionState == "connected":      
            if all([member.pc for member in room.members]) \
                and all([member.pc.connectionState == "connected" for member in room.members]):
                await black_hole.stop()
                text = (
                    "● **Подключенно!**"
                )
                await room.send_to_discord(text)
                for member in room.members:
                    await member.redirect.start()
                await room.connect_voice()   
            else:
                await black_hole.start() 
            payload = {
                "type":"peer-connection",
                "connectionId":client.get_connection_id(),
                "connection":True,
            }
            log.info("Connection state change to *connected*")
            await client.emit("event", data=payload)

    @pc.on("track")
    async def on_track(track) -> None:
        room.add_members_track(track, client)
        black_hole.addTrack(track)            
        log.info("User received a track.")
        payload = {
            "type":"stream-received",
            "connectionId":client.get_connection_id()
        }
        await client.emit("event", data=payload)
    
    if initiator:
        pc.addTrack(redirect.audio)
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)
        payload = {
            "type":"peer-mute",
            "connectionId":client.get_connection_id(),
            "muted":False
        }
        await client.emit("event", data=payload)
        payload = {
            "type":"offer",
            "offer":json.dumps({"sdp":offer.sdp, "type": offer.type}),
            "connectionId":client.get_connection_id(),
        }
        await client.emit("event", data=payload)

async def on_offer(
    client: Client, 
    payload: Dict[str, Any],
    redirect: MediaRedirect,
    pc: RTCPeerConnection,
    room: Room,
) -> None:
    log = client.log
    log.info("Received offer.")
    offer = json.loads(payload.get("offer"))
    remote_description = RTCSessionDescription(
        sdp=offer.get("sdp"),
        type=offer.get("type")
    )
    await pc.setRemoteDescription(remote_description)

    pc.addTrack(redirect.audio)
    answer = await pc.createAnswer()
    await pc.setLocalDescription(answer)
    payload = {
        "type":"answer",
        "answer": json.dumps({"sdp":answer.sdp, "type": answer.type}),
        "connectionId":client.get_connection_id(),
    }
    log.info("Sent answer.")
    await client.emit("event", data=payload)
    with suppress(AttributeError):
        if all([member.client.get_connection_id() for member in room.members]):
            for member in room.members:
                await room.send_ice_candidates(member.pc, member.client)

async def on_answer(
    client: Client, 
    payload: Dict[str, Any],
    redirect: MediaRedirect,
    pc: RTCPeerConnection,
    room: Room,
) -> None:
    log = client.log
    log.info("Received answer.") 
    answer = json.loads(payload.get("answer"))
    remote_description = RTCSessionDescription(
        sdp=answer.get("sdp"),
        type=answer.get("type")
    )
    await pc.setRemoteDescription(remote_description)
    with suppress(AttributeError):
        if all([member.client.get_connection_id() for member in room.members]):
            for member in room.members:
                await room.send_ice_candidates(member.pc, member.client)

async def on_ice_candidate(
    client: Client, 
    payload: Dict[str, Any],
    redirect: MediaRedirect,
    pc: RTCPeerConnection,
    room: Room,
) -> None:        
    log = client.log
    log.info("Received ice candidate")
    candidate_payload = json.loads(payload.get("candidate")).get("candidate")
    candidate = candidate_from_sdp(
        candidate_payload.get("candidate")
    )
    candidate.sdpMid = candidate_payload.get("sdpMid")
    candidate.sdpMLineIndex = candidate_payload.get("sdpMLineIndex")
    await pc.addIceCandidate(candidate)

def register_peer_handlers(client: Client) -> None:
    client.add_action(name="peer-connect", callback=on_peer)
    client.add_action(name="offer", callback=on_offer)
    client.add_action(name="answer", callback=on_answer)
    client.add_action(name="ice-candidate", callback=on_ice_candidate)