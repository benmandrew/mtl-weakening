from __future__ import annotations

import json
import typing


def parse_state(s: str) -> str:
    first, second = s.split("=")
    assert first == "state"
    return second


def parse_variables(s: str) -> dict[str, int | str]:
    return typing.cast("dict[str, int | str]", json.loads(s))


def parse_trace(s: str) -> list[dict[str, int | str]]:
    lines = s.strip().split("\n")
    states = []
    state_name = None
    for line in lines:
        if line.startswith("state="):
            state_name = parse_state(line)
        else:
            assert state_name is not None
            state = parse_variables(line)
            state["state"] = state_name
            states.append(state)
    return states
