from __future__ import annotations

import typing

from defusedxml import ElementTree

from src import marking, util

if typing.TYPE_CHECKING:
    from xml.etree.ElementTree import Element  # nosec B405


def parse(s: str) -> marking.Trace:
    return xml_to_trace(ElementTree.fromstring(s))


def _parse_state(state: Element) -> dict[str, util.Value]:
    state_dict = {}
    for item in state:
        assert item.text is not None
        state_dict[item.attrib["variable"]] = util.str_to_value(
            item.text,
        )
    return state_dict


class NoLoopError(Exception):
    pass


def _parse_loops(loops: Element) -> int:
    if loops.text is None:
        raise NoLoopError
    text = loops.text.strip()
    if text == "":
        raise NoLoopError
    return int(text)


def xml_to_trace(xml_element: Element) -> marking.Trace:
    states: list[dict[str, util.Value]] = []
    loop: int | None = None
    for node in xml_element:
        if node.tag == "node":
            states.append(_parse_state(node[0]))
        elif node.tag == "loops":
            loop = _parse_loops(node)
        else:
            util.eprint(f"Unexpected tag {node.tag} in XML trace")
    if loop is None:
        raise NoLoopError
    assert 0 <= loop < len(states)
    return marking.Trace(states, loop)
