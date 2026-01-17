import networkx as nx
from gerrychain import Partition, Graph, updaters, Election
from gerrychain.proposals import recom
from gerrychain.tree import recursive_tree_part
from gerrychain.constraints import contiguous
from gerrychain.optimization import Gingleator
from functools import partial
import random
import os

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

def safe_reward_partial_dist(part, minority_perc_col, threshold):
    """Gingleator score function that rewards all opportunity districts plus partial credit for
    the next highest district below threshold.

    As opposed to the function currently present in GerryChain, this function won't throw an
    error if no districts are below threshold. If no such district exists, returns number of
    opportunity districts.

    Args:
        part (Partition): GerryChain Partition object.
        minority_perc_col (str): Column name for minority percentage.
        threshold (float): Threshold for minority percentage.
    """
    try:
        return Gingleator.reward_partial_dist(
            part=part, minority_perc_col=minority_perc_col, threshold=threshold
        )
    except ValueError:
        return Gingleator.num_opportunity_dists(
            part=part, minority_perc_col=minority_perc_col, threshold=threshold
        )


def main():
    """
    For each individual grid map, and for each building block size 2, 3, 4, and 6,
    generates dual graphs for 100 partitions of that grid map into pieces of that size.
    Does this by by generating 1,000,000 possible partitions and saving every 10,000th sample.

    Uses short bursts algorithm to gerrymander these building block graphs in favor of Democrats,
    i.e. maximize the number of building blocks for which over 50% of the units are Democratic.
    """
    random_seed_num = 211
    random.seed(random_seed_num)
    pop_col = "population"

    # Iterate over grid map, block size
    for num_r_units in [58, 72, 86]:
        for map_number in [1, 2, 3]:
            for block_size in [2, 3, 4, 6]:

                # Access dual graph for grid map
                grid_dual_graph_file = (
                    f"{SCRIPT_DIR}/../syn_files/syn_unit_maps/map_.jsons/"
                    f"r_units_{num_r_units}_map_{map_number}.json"
                )

                grid_graph = Graph.from_json(grid_dual_graph_file)

                # Set updaters for use later
                my_updaters = {
                    "population": updaters.Tally("population"),
                    "election": Election("election", {"D": "D", "R": "R"}),
                    "R_tally": updaters.Tally("R", alias="R_tally"),
                    "D_tally": updaters.Tally("D", alias="D_tally"),
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
                            method=recursive_tree_part,
                        )
                        assert all(init_part.assignment.to_series().value_counts() == block_size)
                        partition_4_lst.append(init_part.assignment.to_dict())
                        n_found += 1
                    except Exception:
                        pass

                # Value to be optimized toward
                num_dem_seats = lambda p: p["election"].seats("D")

                proposal = partial(
                    recom, pop_col=pop_col, pop_target=block_size, epsilon=0, node_repeats=2
                )

                recom_chain = Gingleator(
                    proposal=proposal,
                    constraints=[contiguous],
                    threshold=0.5,
                    initial_state=init_part,
                    total_pop_col="population",
                    minority_pop_col="D_tally",
                    score_function=safe_reward_partial_dist
                )

                # Save every 10,000th sample
                samples = []
                for i, partition in enumerate(
                    recom_chain.short_bursts(20, round(1000000 / 20))
                ):
                    if (i + 1) % 10000 == 0:
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
                    # as a quotient graph of the original grid dual graph
                    subgraph = nx.quotient_graph(grid_graph, list(district_units_dict.values()))
                    subgraph = nx.convert_node_labels_to_integers(subgraph)
                    gerry_subgraph = Graph.from_networkx(subgraph)
                    gerry_subgraph.nodes(data=True)

                    # Save important node attribute info to building block dual graph
                    for block, data in gerry_subgraph.nodes(data=True):
                        units = data["graph"].nodes
                        gerry_subgraph.nodes[block]["units"] = str(units)
                        gerry_subgraph.nodes[block]["population"] = block_size
                        gerry_subgraph.nodes[block]["id"] = '"' + str(block) + '"'

                        d_votes = 0
                        r_votes = 0
                        for unit in units:
                            d_votes = d_votes + grid_graph.nodes[unit]['D']
                            r_votes = r_votes + grid_graph.nodes[unit]['R']
                        gerry_subgraph.nodes[block]['D'] = d_votes
                        gerry_subgraph.nodes[block]['R'] = r_votes

                    # Save building block file
                    save_to_file = (
                        f"{SCRIPT_DIR}/../syn_files/syn_building_block_partitions/gerry/"
                        f"r_units_{num_r_units}_map_{map_number}/block_size_{block_size}/sample_{i+1}.json"
                    )
                    os.makedirs(os.path.dirname(save_to_file), exist_ok=True)
                    gerry_subgraph.to_json(save_to_file)

main()