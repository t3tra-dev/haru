from typing import Callable


def Object():

    class prototype:

        def __init__(self) -> None:
            return None

        def __defineGetter__(self, prop: str, func: Callable) -> None:
            return None

        def __defineSetter__(self, prop: str, func: Callable) -> None:
            return None

        def __lookupGetter__(self, prop: str) -> Callable | None:
            ...

        def __lookupSetter__(self, prop: str) -> Callable | None:
            ...

        @property
        def __proto__(self) -> None:
            return None
