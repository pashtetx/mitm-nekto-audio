from typing import Dict, Any, Union, Callable, Awaitable
from types import FunctionType, CoroutineType

class Dispatcher:

    def __init__(self) -> None:
        self.actions = {}

    def add_action(self, name: str, callback: Union[Callable, Awaitable]) -> None:
        if not self.actions.get(name): self.actions[name] = list()
        if not callable(callback): raise ValueError("callback is not callable")
        self.actions[name].append(callback)

    async def dispatch(self, name: str, payload: Dict[str, Any]) -> None:
        actions = self.actions.get(name)
        if not actions: return
        for action in actions:
            if isinstance(action, CoroutineType):
                await action(payload)
            elif isinstance(action, FunctionType):
                action(payload)
            
