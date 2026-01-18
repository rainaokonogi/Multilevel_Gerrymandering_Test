from gerrychain import (Partition, Graph, MarkovChain, updaters, accept, Election)
from gerrychain.proposals import recom
from gerrychain.tree import recursive_tree_part
from gerrychain.constraints import contiguous
from gerrychain.optimization import Gingleator
from functools import partial
import random
import ast
import os
from pyben import PyBenEncoder
import jsonlines as jl

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


def run_experiment_ng(num_r_units, map_number, block_size, init_part, random_seed, total_steps):
    """Run experiment where the building blocks are not gerrymandered but the resulting map is.

    Args:
        num_r_units (int): Number of Republican units in underlying map (e.g., 58, 72, 86).
        map_number (int): Map number to use (1-9).
        block_size (int): Size of building blocks (e.g., 2, 3, 4, 6).
        init_part (int): Number of initial district partition to use for Markov chain (1–3)
        random_seed (int): Random seed for reproducibility.
        total_steps (int): Total number of steps for each chain.
    """

    # Load data from underlying map as graph
    # Will use this to put vote totals onto block graph
    underlying_map = (
        f"{SCRIPT_DIR}/syn_unit_maps/map_.jsons/"
        f"r_units_{num_r_units}_map_{map_number}.json"
    )
    underlying_graph = Graph.from_json(underlying_map)

    # Set pop data, random seed
    random.seed(random_seed)
    pop_col = 'population'

    # Iterate over building block files
    for sample in range(1,101):

        save_assignment_results_to = (
            f"{SCRIPT_DIR}/../output_ensembles/NG/r_units_{num_r_units}_map_{map_number}/block_size_{block_size}/"
            f"sample_{sample}/init_part_{init_part}_random_seed_{random_seed}_burst_length_20_steps_{total_steps}_assignment.ben"
        )
        save_updaters_results_to = (
            f"{SCRIPT_DIR}/../output_stats/NG/r_units_{num_r_units}_map_{map_number}/block_size_{block_size}/"
            f"sample_{sample}/init_part_{init_part}_random_seed_{random_seed}_burst_length_20_steps_{total_steps}_updaters.jsonl"
        )
        os.makedirs(os.path.dirname(save_assignment_results_to), exist_ok=True)
        os.makedirs(os.path.dirname(save_updaters_results_to), exist_ok=True)

        block_data = (
            f"{SCRIPT_DIR}/syn_building_block_partitions/neutral/"
            f"block_size_{block_size}/sample_{sample}.json"
        )

        block_graph = Graph.from_json(block_data)

        # For use later when saving results
        graph_node_order = list(block_graph.nodes)

        # Use data from underlying map to add vote totals for each building block to block graph
        block_to_nodes_dict = {}

        for block, data in block_graph.nodes(data=True):
            if "units" in data:
                block_to_nodes_dict[block] = ast.literal_eval(data["units"])

        for block in block_graph.nodes:
            d_votes = 0
            r_votes = 0
            nodes_in_block = block_to_nodes_dict[block]
            for node in nodes_in_block:
                d_votes = d_votes + underlying_graph.nodes[node]['D']
                r_votes = r_votes + underlying_graph.nodes[node]['R']
            block_graph.nodes[block]['D'] = d_votes
            block_graph.nodes[block]['R'] = r_votes

        # Updaters
        my_updaters = {
            "population": updaters.Tally("population",alias="population"),
            "election": Election("election", {"D": "D", "R": "R"}),
            "R_tally": updaters.Tally("R",alias="R_tally"),
            "D_tally": updaters.Tally("D",alias="D_tally"),
            }

        # Pull initial partition from block graph
        initial_partition = Partition(
            block_graph,
            assignment=f"init_part_{init_part}",
            updaters=my_updaters
        )

        # 144 nodes and 12 districts, so pop_target is 12
        proposal = partial(
            recom,
            pop_col=pop_col,
            pop_target=12,
            epsilon=0,
            node_repeats=2
        )

        # Define recom chain
        # Gingleator score function should return number of districts where over 50% of the votes go to gerrymandered party
        # + percentage of that party in district where it gets the highest vote share under 50%
        recom_chain = Gingleator(
            proposal=proposal,
            constraints=[contiguous],
            threshold=0.5,
            initial_state=initial_partition,
            total_pop_col='population',
            minority_pop_col='D_tally',
            score_function=safe_reward_partial_dist
        )

        # Save results
        with (
                PyBenEncoder(save_assignment_results_to, overwrite=True) as encoder,
                jl.open(save_updaters_results_to, "w") as updater_output_file,
            ):
        
            for i, plan in enumerate(recom_chain.short_bursts(5,round(total_steps/5))):

                assert (
                    plan is not None
                ), "Something went terribly wrong. There is no output partition."

                assignment_series = plan.assignment.to_series()
                ordered_assignment = (
                    assignment_series.loc[graph_node_order].astype(int).tolist()
                )
                encoder.write(ordered_assignment)

                election = plan["election"]
                
                seats_won = {
                    "D": election.seats("D"),
                    "R": election.seats("R")
                }

                regions = election.regions 

                d_counts = election.counts("D")
                r_counts = election.counts("R")
                d_votes_by_district = dict(zip(regions, d_counts))
                r_votes_by_district = dict(zip(regions, r_counts))

                district_winners = {region: ("D" if d > r else "R") for region, d, r in zip(regions, d_counts, r_counts)}

                record = {
                    "step": i,
                    "population": dict(plan["population"]),
                    "Seats won": seats_won,
                    "D votes": d_votes_by_district,
                    "R votes": r_votes_by_district,
                    "District winners": district_winners
                }

                updater_output_file.write(record)