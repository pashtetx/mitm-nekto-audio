from core.client import Client
from typing import Dict, Any
from utils import alarm

async def on_connect(client: Client, payload: Dict[str, Any]) -> None:
    payload = {
        "type":"register",
        "android":False,
        "version":20,
        "userId":client.user_id,
        "timeZone":client.time_zone,
        "locale":client.locale
    }
    if client.is_firefox:
        payload.update({"firefox":client.is_firefox})
    await client.emit("event", data=payload)
    client.log.info("User sent register payload.")

async def on_error(client: Client, payload: Dict[str, Any], *args, **kwargs) -> None:
    client.log.critical(
        "Unknown error {}: {}".format(
            payload.get("id"), 
            payload.get("description")
        )
    )

async def on_auth(client: Client, payload: Dict[str, Any]) -> None:
    internal_id = payload.get("internal_id")
    webagent = alarm(client.user_id, internal_id)
    payload = {
        "type":"web-agent",
        "data":webagent
    }
    await client.emit("event", data=payload)
    client.log.info("User sent web-agent payload.", payload=payload)
    await client.search()

async def on_peer(client: Client, payload: Dict[str, Any], *args, **kwargs) -> None:
    client.set_connection_id(payload.get("connectionId"))

async def on_close(client: Client, payload: Dict[str, Any], *args, **kwargs) -> None:
    client.set_connection_id(None)

def register_client_handlers(client: Client) -> None:
    client.add_action(name="connect", callback=on_connect)
    client.add_action(name="registered", callback=on_auth)
    client.add_action(name="peer-connect", callback=on_peer)
    client.add_action(name="peer-disconnect", callback=on_close)