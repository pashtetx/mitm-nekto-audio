from socketio import AsyncClient

class Transport(AsyncClient):
    
    endpoint = "wss://audio.nekto.me"

    async def connect(self, ua: str) -> None:
        await super().connect(
            self.endpoint,
            transports=["websocket"],
            socketio_path="websocket"
        )