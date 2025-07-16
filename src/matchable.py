from dataclasses import fields
from typing import TypeVar, Any, cast

T = TypeVar("T", bound=type)


def matchable(cls: T) -> T:
    cls_any = cast(Any, cls)
    setattr(cls_any, "__match_args__", tuple(f.name for f in fields(cls)))
    return cls
