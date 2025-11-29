import random
from pathlib import Path

import graphviz


def random_graph(
    n_nodes: int, edge_probability: float, node_pairs: list[tuple[str, str]],
) -> dict[int, list[int]]:
    adj: dict[int, list[int]] = {i: [] for i in range(n_nodes)}
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j and random.random() < edge_probability:
                adj[i].append(j)
    for start_node, end_node in node_pairs:
        start_index = int(start_node[1:])
        end_index = int(end_node[1:])
        if end_index not in adj[start_index]:
            adj[start_index].append(end_index)
    for k in adj:
        adj[k] = list(filter(lambda x: x != 0, adj[k]))
    adj[0] = [i for i in range(1, n_nodes)]
    return adj


def random_loop_graph(
    n_loop_nodes: int, n_aux_nodes, edge_probability: float,
) -> dict[int, list[int]]:
    adj: dict[int, list[int]] = {
        i: [] for i in range(n_loop_nodes + n_aux_nodes)
    }
    for i in range(n_loop_nodes):
        adj[i].append((i + 1) % n_loop_nodes)
    for i in range(n_loop_nodes + n_aux_nodes):
        for j in range(n_loop_nodes + n_aux_nodes):
            if i < n_loop_nodes and j < n_loop_nodes:
                continue
            if i != j and random.random() < edge_probability:
                adj[i].append(j)
    return adj


def graph_to_smv(adj: dict[int, list[int]]) -> str:
    nodes = list(adj.keys())
    out: list[str] = [
        "MODULE main",
        "VAR",
        "    node : {" + ", ".join(f"n{i}" for i in nodes) + "};",
        "DEFINE",
    ]

    for i in nodes:
        out.append(f"    p{i} := node = n{i};")
    out.extend(
        [
            "ASSIGN",
            "    init(node) := n0;",
            "    next(node) := case",
        ],
    )
    for i in nodes:
        succ = adj[i]
        if succ:
            out.append(
                f"        node = n{i} : "
                "{" + ", ".join(f"n{j}" for j in succ) + "};",
            )
    out.extend(
        [
            "        TRUE : node;",
            "    esac;\n",
        ],
    )
    return "\n".join(out)


def export_graph(
    adj: dict[int, list[int]],
    filename: Path = Path("graph.smv"),
) -> None:
    with filename.open(mode="w", encoding="utf-8") as f:
        f.write(graph_to_smv(adj))


def graph_to_dot(adj: dict[int, list[int]]) -> str:
    nodes = sorted(adj.keys())
    out: list[str] = [
        "digraph G {",
        "    rankdir=LR;",
        "    node [shape=circle];",
    ]
    for i in nodes:
        out.append(f'    n{i} [label="{i}"];')
    for i in nodes:
        for j in adj[i]:
            out.append(f"    n{i} -> n{j};")
    out.append("}")
    return "\n".join(out)


def show_graph(adj: dict[int, list[int]]) -> None:
    graphviz.Source(graph_to_dot(adj)).render(view=True)
