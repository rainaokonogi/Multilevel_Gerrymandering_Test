from gerrychain import Partition, Graph, updaters
from gerrychain.tree import recursive_tree_part
import random
import os
from networkx.readwrite import json_graph
from pathlib import Path
import json

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

random_seed_num = 572
random.seed(random_seed_num)

def main():
    """
    For each gerrymandered building block graph, finds three initial partitions
    (assignments of blocks to districts).
    Overwrites the block graph with a new graph where these initial partition are saved as
    node attributes "init_part_1", "init_part_2", and "init_part_3".
    """

    gerry_blocks_dir = (
            f"{SCRIPT_DIR}/../syn_files/syn_building_block_partitions/gerry"
        )

    file_count = 0

    # Iterate over gerrymandered building block graphs
    for json_file in Path(gerry_blocks_dir).rglob("*.json"):
        file_count += 1

        if file_count % 100 == 0:
            print(f"Processed {file_count} files (out of 3600)")

        level_2 = json_file.parent.name
        level_1 = json_file.parent.parent.name
        file_name = f"{gerry_blocks_dir}/{level_1}/{level_2}/{json_file.name}"
        # new_file = f"/share/duchin/raina/final_exp_files/final building block graphs with init parts/gerry/{level_1}/{level_2}/{json_file.name}"
        # os.makedirs(os.path.dirname(new_file), exist_ok=True)

        graph = Graph.from_json(file_name)

        my_updaters = {
            "population": updaters.Tally("population",alias="population"),
            "R_tally": updaters.Tally("R",alias="R_tally"),
            "D_tally": updaters.Tally("D",alias="D_tally")
            }

        # Find three initial partitions
        for i in [1,2,3]:
            n_found = 0
            while n_found < 1:
                try:
                    init_part_i = Partition.from_random_assignment(
                        graph=graph,
                        n_parts=12,
                        pop_col='population',
                        updaters = my_updaters,
                        epsilon = 0.00001,
                        method = recursive_tree_part
                    )
                    n_found += 1
                except Exception:
                    pass
            
            assignment_i = init_part_i.assignment

            for block, district in assignment_i.items():
                graph.nodes[block][f"init_part_{i}"] = district

        # Overwrite file with graph with initial partitions added
        with open(file_name, "w") as f:
            json.dump(json_graph.adjacency_data(graph), f)

main()