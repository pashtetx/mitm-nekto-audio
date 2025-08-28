from socketio import AsyncClient

class Transport(AsyncClient):
    
    endpoint = "wss://audio.nekto.me/"

    async def connect(self, ua: str, wait: bool = True) -> None:
        await super().connect(
            self.endpoint,
            transports=["websocket"],
            socketio_path="websocket",
            headers={"User-Agent":ua},
        )
        if wait:
            await super().wait()