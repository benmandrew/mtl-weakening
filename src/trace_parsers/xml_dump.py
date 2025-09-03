from xml.etree.ElementTree import Element  # nosec B405

from defusedxml import ElementTree

from src import marking, util


def parse(s: str) -> Element:
    return ElementTree.fromstring(s)


def xml_to_trace(xml_element: Element) -> marking.Trace:
    states: list[dict[str, util.Value]] = []
    for node in xml_element:
        state_dict = {}
        if node.tag == "node":
            state = node[0]
            for item in state:
                assert item.text is not None
                state_dict[item.attrib["variable"]] = util.str_to_value(
                    item.text,
                )
            states.append(state_dict)
    return marking.Trace(states)
