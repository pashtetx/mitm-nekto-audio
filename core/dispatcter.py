from typing import Dict, Any, Union, Callable, Awaitable
from inspect import iscoroutinefunction

class Dispatcher:

    def __init__(self, default: Dict[str, Any] = {}) -> None:
        self.actions = {}
        self.default = default

    def add_action(self, name: str, callback: Union[Callable, Awaitable]) -> None:
        if not self.actions.get(name): self.actions[name] = list()
        if not callable(callback): raise ValueError("callback is not callable")
        self.actions[name].append(callback)

    async def dispatch_connect(self) -> None:
        await self.dispatch("connect", {})

    async def dispatch_socketio(self, payload: Dict[str, Any]) -> None:
        type = payload.get("type")
        await self.dispatch(type, payload)

    async def dispatch(self, name: str, payload: Dict[str, Any]) -> None:
        print(payload)
        actions = self.actions.get(name)
        if not actions: return
        for action in actions:
            if iscoroutinefunction(action):
                await action(**self.default, payload=payload)
            else:
                action(**self.default, payload=payload)
            
