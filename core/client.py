from .dispatcter import Dispatcher

from typing import Callable, Awaitable, Union, Dict, Any, Optional

from socketio import AsyncClient

from log import log

class Client(AsyncClient):

    endpoint: str = "wss://audio.nekto.me/"

    def __init__(
        self, 
        user_id: str,
        ua: str,
        locale: str = "en",
        time_zone: str = "Europe/Berlin",
        search_criteria: Dict[str, Any] = {
            "peerSex": "ANY",
            "group": 0,
            "userSex": "ANY"
        },
        *args,
        **kwargs,
    ) -> None:
        self.user_id = user_id
        self.ua = ua
        self.locale = locale
        self.time_zone = time_zone
        self.search_criteria = search_criteria
        self.is_firefox = "Gecko" in self.ua

        self.connection_id = None
        super().__init__(logger=False, *args, **kwargs)
        self.log = log.bind(user_id=user_id[:7])
        self.dispatcher = Dispatcher(default={"client":self})

    def set_connection_id(self, value: Union[str, None]) -> None:
        self.connection_id = value

    def get_connection_id(self) -> Optional[str]:
        if self.connection_id: return self.connection_id
        raise AttributeError("Client not connected.")

    def add_action(self, name: str, callback: Union[Callable, Awaitable]) -> None:
        self.dispatcher.add_action(name, callback)

    def remove_action(self, name: str) -> None:
        self.dispatcher.remove_action(name)

    async def search(self) -> None:
        self.log.info(
            "User is searching for a voice partner.", criteria=self.search_criteria
        )
        payload = {
            "type":"scan-for-peer",
            "peerToPeer":True,
            "token":None,
            "searchCriteria":self.search_criteria
        }
        await self.emit("event", data=payload)

    async def peer_disconnect(self) -> None:
        try:
            connection_id = self.get_connection_id()
            self.log.info("User disconnect a peer", connection_id=connection_id)
            await self.emit(
                "event", data={
                    "type":"peer-disconnect",
                    "connectionId":connection_id
                }
            )
        except AttributeError:
            self.log.info("User stops scanning")
            await self.emit("event", data={
                "type":"stop-scan"
            })
            
    async def connect(self, wait: bool = True) -> None:
        self.on("connect", self.dispatcher.dispatch_connect)
        self.on("event", self.dispatcher.dispatch_socketio)
        await super().connect(
            self.endpoint,
            transports=["websocket"],
            socketio_path="websocket",
            headers={"User-Agent":self.ua},
        )
        if wait:
            await super().wait()
