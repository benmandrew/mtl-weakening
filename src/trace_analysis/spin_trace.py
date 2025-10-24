from __future__ import annotations

import json
import typing
from collections import OrderedDict

from src import marking


def parse_variables(s: str) -> dict[str, int | str]:
    return typing.cast("dict[str, int | str]", json.loads(s))


def expand_state(
    state: dict[str, int | str],
    state_values: OrderedDict[str, None],
) -> dict[str, int]:
    expanded: dict[str, int] = {}
    for k, v in state.items():
        if isinstance(v, int):
            expanded[k] = v
        elif isinstance(v, str):
            for val in state_values:
                expanded[f"{val}_p"] = v == val
        else:
            msg = f"Unexpected variable type: {type(v)}"
            raise TypeError(msg)
    return expanded


def clear_nonappearing_states(
    states: list[dict[str, int]],
    state_values: OrderedDict[str, None],
) -> None:
    state_variables = {f"{val}_p" for val in state_values}
    for var in state_variables:
        appears = any(state.get(var, 0) == 1 for state in states)
        if not appears:
            for state in states:
                state.pop(var)


def get_state_values(
    states: list[dict[str, int | str]],
) -> OrderedDict[str, None]:
    state_values: OrderedDict[str, None] = OrderedDict()
    for state in states:
        for k, v in state.items():
            if isinstance(v, str) and k == "state":
                state_values[v] = None
    return state_values


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
    state_values = get_state_values(states)
    expanded_states = [expand_state(state, state_values) for state in states]
    clear_nonappearing_states(expanded_states, state_values)
    return marking.Trace(
        typing.cast("list[dict[str, bool | int | str]]", expanded_states),
        loop_i,
    )
