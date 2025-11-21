import random


def random_graph(n_nodes: int, edge_probability: float) -> dict[int, list[int]]:
    adj: dict[int, list[int]] = {i: [] for i in range(n_nodes)}
    for i in range(n_nodes):
        for j in range(n_nodes):
            if i != j and random.random() < edge_probability:
                adj[i].append(j)
    return adj


def graph_to_smv(adj: dict[int, list[int]]) -> str:
    nodes = list(adj.keys())
    out: list[str] = [
        "MODULE main",
        "VAR",
        "    node : {" + ", ".join(f"n{i}" for i in nodes) + "};",
        "",
        "ASSIGN",
        "    init(node) := n0;",
        "    next(node) := case",
    ]
    for i in nodes:
        succ = adj[i]
        if succ:
            out.append(f"        node = n{i} : " +
                    "{" + ", ".join(f'n{j}' for j in succ) + "};")
        else:
            out.append(f"        node = n{i} : n{i};")
    out.append("        esac;\n")
    return "\n".join(out)

def export_graph(adj: dict[int, list[int]], filename="graph.smv") -> None:
    with open(filename, "w") as f:
        f.write(graph_to_smv(adj))
