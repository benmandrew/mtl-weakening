import random

from src.logic import mtl


def generate_formulae(
    n_nodes: int, interval_range: tuple[int, int], n_formulae: int,
) -> tuple[list[mtl.Mtl], list[tuple[str, str]]]:
    formulae: list[mtl.Mtl] = []
    node_pairs: list[tuple[str, str]] = []
    for _ in range(n_formulae):
        end_i = random.randint(interval_range[0], interval_range[1])
        start_i = random.randint(interval_range[0], end_i)
        start_node = f"p{random.randint(0, n_nodes - 1)}"
        end_node = f"p{random.randint(0, n_nodes - 1)}"
        while end_node == start_node:
            end_node = f"p{random.randint(0, n_nodes - 1)}"
        node_pairs.append((start_node, end_node))
        formulae.append(
            mtl.Always(
                mtl.Implies(
                    mtl.Prop(start_node),
                    # mtl.Eventually(mtl.Prop(end_node), (start_i, end_i)),
                    mtl.Eventually(mtl.Prop(end_node), (0, 0)),
                ),
            ),
            # mtl.Always(
            #     mtl.Implies(
            #         mtl.And(mtl.Prop(start_node), mtl.Next(mtl.Not(mtl.Prop(start_node)))),
            #         mtl.Always(mtl.Not(mtl.Prop(end_node)), (0, n_nodes)),
            #     ),
            # ),
        )
    return formulae, node_pairs
