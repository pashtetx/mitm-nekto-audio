from .dispatcter import Dispatcher
from .transport import Transport

from typing import Callable, Awaitable, Union, Dict, Any

from functools import partial

from utils import alarm

class Client:

    def __init__(
        self, 
        user_id: str,
        ua: str,
        locale: str = "en",
        time_zone: str = "Europe/Kiew"
    ) -> None:
        self.user_id = user_id
        self.ua = ua
        self.locale = locale
        self.time_zone = time_zone

        self.is_firefox = "Gecko" in self.ua

        self.transport = Transport()
        self.dispatcher = Dispatcher(default={"transport":self.transport})

    def add_action(self, name: str, callback: Union[Callable, Awaitable]) -> None:
        self.dispatcher.add_action(name, callback)

    def init_actions(self) -> None:
        self.add_action(name="connect", callback=self.__on_connect)
        self.add_action(name="registered", callback=self.__on_auth)

    async def __on_connect(self, transport: Transport, payload: Dict[str, Any]) -> None:
        payload = {
            "type":"register",
            "android":False,
            "version":20,
            "userId":self.user_id,
            "timeZone":self.time_zone,
            "locale":self.locale
        }
        if self.is_firefox:
            payload.update({"firefox":self.is_firefox})
        await transport.emit("event", data=payload)

    async def __on_auth(self, transport: Transport, payload: Dict[str, Any]) -> None:
        internal_id = payload.get("internal_id")
        webagent = alarm(self.user_id, internal_id)
        payload = {
            "type":"web-agent",
            "data":webagent
        }
        await self.transport.emit("event", data=payload)

    async def connect(self) -> None:
        self.init_actions()
        self.transport.on("connect", self.dispatcher.dispatch_connect)
        self.transport.on("event", self.dispatcher.dispatch_socketio)
        await self.transport.connect(ua=self.ua)