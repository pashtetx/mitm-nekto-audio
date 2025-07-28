from .dispatcter import Dispatcher
from .transport import Transport

from typing import Callable, Awaitable, Union, Dict, Any

from functools import partial

class Client:

    def __init__(
        self, 
        token: str,
        ua: str,
        locale: str = "en",
        time_zone: str = "Europe/Kiew"
    ) -> None:
        self.token = token
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

    async def __on_connect(self, transport: Transport, payload: Dict[str, Any]) -> None:
        payload = {
            "type":"register",
            "android":False,
            "version":20,
            "userId":self.token,
            "timeZone":self.time_zone,
            "locale":self.locale
        }
        if self.is_firefox:
            payload.update({"firefox":self.is_firefox})
        print(payload)
        await transport.emit("event", data=payload)

    async def connect(self) -> None:
        self.init_actions()
        self.transport.on("connect", self.dispatcher.dispatch_connect)
        self.transport.on("event", self.dispatcher.dispatch_socketio)
        await self.transport.connect(ua=self.ua)