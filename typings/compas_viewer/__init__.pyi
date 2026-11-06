from collections.abc import Callable
from typing import Protocol
from typing import TypeVar

_Callback = TypeVar("_Callback", bound=Callable[[int], None])

class SceneObject(Protocol):
    def update(self, *, update_data: bool = ...) -> None: ...

class Scene(Protocol):
    def add(self, item: object, **kwargs: object) -> SceneObject: ...

class Viewer:
    scene: Scene
    def __init__(self) -> None: ...
    def on(self, *, interval: int) -> Callable[[_Callback], _Callback]: ...
    def show(self) -> None: ...
