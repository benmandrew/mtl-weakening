import subprocess
import tempfile
from pathlib import Path

from src import util
from src.synthetic import random_formula, random_graph

N_NODES: int = 20
N_FORMULAE: int = 5
# EDGE_PROBABILITY: float = 1.0 / float(N_NODES)
EDGE_PROBABILITY: float = 0.02


formulae, node_pairs = random_formula.generate_formulae(
    N_NODES, (0, N_NODES), N_FORMULAE,
)
graph = random_graph.random_loop_graph(N_NODES, N_NODES, EDGE_PROBABILITY)

random_graph.show_graph(graph)

with tempfile.TemporaryDirectory() as tmpdir:
    graph_path = Path(tmpdir) / "graph.smv"
    random_graph.export_graph(graph, graph_path)
    for formula in formulae:
        print(f"Checking: {formula}")
        subprocess.run(
            [
                util.PYTHON3_PATH,
                "-m",
                "src.iterative_weaken",
                "--model-checker",
                "NUXMV",
                "--model",
                graph_path.as_posix(),
                "--de-bruijn",
                "0,1",
                "--mtl",
                f"{formula}",
            ],
            check=False,
        )
        print()
