from __future__ import annotations

import json
import typing

from src import marking
from src.trace_analysis import exceptions


def parse_variables(s: str) -> dict[str, int | str]:
    return typing.cast("dict[str, int | str]", json.loads(s))


def expand_state(state: dict[str, int | str]) -> dict[str, int]:
    expanded: dict[str, int] = {}
    for k, v in state.items():
        if isinstance(v, int):
            expanded[k] = v
        elif isinstance(v, str):
            for enum_value in [
                "resting",
                "leavingHome",
                "randomWalk",
                "moveToFood",
                "scanArena",
                "grabFood",
                "moveToHome",
                "deposit",
                "homing",
            ]:
                expanded[f"{enum_value}"] = 1 if v == enum_value else 0
        else:
            msg = f"Unexpected variable type: {type(v)}"
            raise TypeError(msg)
    return expanded


def clear_nonappearing_states(states: list[dict[str, int]]) -> None:
    for enum_value in [
        "resting",
        "leavingHome",
        "randomWalk",
        "moveToFood",
        "scanArena",
        "grabFood",
        "moveToHome",
        "deposit",
        "homing",
    ]:
        appears = any(state.get(enum_value, 0) == 1 for state in states)
        if not appears:
            for state in states:
                state.pop(enum_value)


def parse(s: str) -> marking.Trace:
    lines = s.strip().split("\n")
    states: list[dict[str, int | str]] = []
    state_i = 0
    loop_i: int | None = None
    for line in lines:
        if line.startswith("START OF CYCLE"):
            assert loop_i is None
            loop_i = state_i - 1
        else:
            states.append(parse_variables(line))
            state_i += 1
    if loop_i is None:
        raise exceptions.NoLoopError
    expanded_states = [expand_state(state) for state in states]
    clear_nonappearing_states(expanded_states)
    return marking.Trace(
        typing.cast("list[dict[str, bool | int | str]]", expanded_states), loop_i,
    )
