import networkx as nx
from gerrychain import Partition, Graph, MarkovChain, updaters, accept
from gerrychain.proposals import recom
from gerrychain.tree import recursive_tree_part
from gerrychain.constraints import contiguous
from gerrychain.accept import always_accept
from functools import partial
import random
import os

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

def main():
    """
    For each building block size 2, 3, 4, and 6, creates 100 partitions of a 12x12 grid into pieces of that size.
    Does this by by generating 1,000,000 possible partitions and saving every 10,000th sample.
    """

    random_seed_num = 346
    random.seed(random_seed_num)
    pop_col = "population"

    # Iterate over block sizes
    for block_size in [2, 3, 4, 6]:

        # Load 12x12 grid
        grid_dual_graph_file = (
            f"{SCRIPT_DIR}/../syn_files/syn_unit_maps/"
            f"12x12_grid_no_votes.json"
        )
        grid_graph = Graph.from_json(grid_dual_graph_file)        

        # Set updaters for use later
        my_updaters = {
            "population": updaters.Tally("population")
        }

        # Find initial partition of grid map into pieces of size block_size
        partition_4_lst = []
        n_found = 0
        while n_found < 1:
            try:
                init_part = Partition.from_random_assignment(
                    graph=grid_graph,
                    n_parts=144 // block_size,
                    pop_col="population",
                    updaters=my_updaters,
                    epsilon=0.00001,
                    method=recursive_tree_part
                )
                assert all(init_part.assignment.to_series().value_counts() == block_size)
                partition_4_lst.append(init_part.assignment.to_dict())
                n_found += 1
            except Exception:
                pass

        proposal = partial(
            recom, pop_col=pop_col, pop_target=block_size, epsilon=0, node_repeats=2
        )

        recom_chain = MarkovChain(
            proposal=proposal,
            constraints=[contiguous],
            initial_state=init_part,
            accept=always_accept,
            total_steps=1000000
        )

        # Save every 10,000th sample
        samples = []
        for i, partition in enumerate(recom_chain):
            if (i+1) % 10000 == 0:
                partition_info = partition.assignment.to_dict()
                samples.append(partition_info)
                print(f"collected sample! (i = {int((i+1) / 10000)})")
            else:
                continue
            
        print(f"Collected {len(samples)} samples.")

        # Each sample is saved as a dictionary mapping units to districts
        # Convert these into dictionaries mapping districts to lists of units
        for i in range(len(samples)):
            district_units_dict = {}
            for node, assign in samples[i].items():
                if assign not in district_units_dict:
                    district_units_dict[assign] = set()
                district_units_dict[assign].add(int(node))

            # Use new dictionary to represent building blocks
            # as a quotient graph of 12x12 grid
            subgraph = nx.quotient_graph(grid_graph, list(district_units_dict.values()))
            subgraph = nx.convert_node_labels_to_integers(subgraph)
            neutral_subgraph = Graph.from_networkx(subgraph)
            neutral_subgraph.nodes(data=True)

            # Save important node attribute info to building block dual graph
            for node, data in neutral_subgraph.nodes(data=True):
                units = data["graph"].nodes
                neutral_subgraph.nodes[node]["units"] = str(units)
                neutral_subgraph.nodes[node]["population"] = block_size
                neutral_subgraph.nodes[node]["id"] = '"' + str(node) + '"'

            # Save building block file
            save_to_file = (
                f"{SCRIPT_DIR}/../syn_files/syn_building_block_partitions/neutral/"
                f"/block_size_{block_size}/sample_{i+1}.json"
            )
            os.makedirs(os.path.dirname(save_to_file), exist_ok=True)
            neutral_subgraph.to_json(save_to_file)

main()