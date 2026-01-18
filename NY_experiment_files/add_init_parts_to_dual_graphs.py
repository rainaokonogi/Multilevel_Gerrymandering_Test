from gerrychain import Partition, Graph, updaters
from gerrychain.tree import recursive_tree_part
import random
import os
from networkx.readwrite import json_graph
import json

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

random_seed = 547
random.seed(random_seed)

def add_init_parts(block_type):
    """For each of the NY dual graphs, finds five initial partitions
    (assignments of units to districts).
    Saves a new dual graph where these initial partition are saved as
    node attributes "init_part_1", "init_part_2", "init_part_3", etc.
    """

    dual_graph_info = (
        f"{SCRIPT_DIR}/NY_dual_graphs/connected_dual_graphs_without_initial_partitions/"
        f"conn_{block_type}_dual_graph.json"
    )

    new_file = (
        f"{SCRIPT_DIR}/NY_dual_graphs/new_connected_dual_graphs_with_initial_partitions/"
        f"conn_{block_type}_dual_graph.json"
    )
    os.makedirs(os.path.dirname(new_file), exist_ok=True)

    dual_graph = Graph.from_json(dual_graph_info)

    # Set pop data, random seed
    pop_col = "TOT_POP"

    my_updaters = {
        "population": updaters.Tally(pop_col, alias="population")
    }

    # Find five initial partitions
    for i in range(1,6):

        n_found = 0
        while n_found < 1:
            try:
                init_part_i = Partition.from_random_assignment(
                    graph=dual_graph,
                    n_parts=63,
                    pop_col=pop_col,
                    updaters=my_updaters,
                    epsilon=0.01,
                    method=recursive_tree_part,
                )
                n_found += 1
            except Exception:
                pass

        assignment = init_part_i.assignment

        # Add initial partition as attribute to dual graph
        for node, district in assignment.items():
            dual_graph.nodes[node][f"init_part_{i}"] = district

        # Write dual graph to new file
    with open(new_file, "w") as f:
        json.dump(json_graph.adjacency_data(dual_graph), f)