from typing import ContextManager, Type


def raises(exception: Type[Exception]) -> ContextManager[Exception]: ...
