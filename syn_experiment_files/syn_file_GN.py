from gerrychain import (Partition, Graph, MarkovChain, updaters, accept, Election)
from gerrychain.proposals import recom
from gerrychain.tree import recursive_tree_part
from gerrychain.constraints import contiguous
from gerrychain.accept import always_accept
from functools import partial
import random
import jsonlines as jl
import ast
import os
from pyben import PyBenEncoder

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

def run_experiment_gn(num_r_units, map_number, block_size, init_part, random_seed, total_steps):
    """Run gerrymandering experiment where the building blocks are gerrymandered but the resulting map is not.

    Args:
        num_r_units (int): Number of Republican units in underlying map (e.g., 58, 72, 86).
        map_number (int): Map number to use (1-9).
        block_size (int): Size of building blocks (e.g., 2, 3, 4, 6).
        init_part (int): Number of initial district partition to use for Markov chain (1–3)
        random_seed (int): Random seed for reproducibility.
        total_steps (int): Total number of steps for each chain.
    """

    # Set pop data, random seed
    random.seed(random_seed)
    pop_col = 'population'

    # Iterate over building block files
    for sample in range(1,101):

        save_assignment_results_to = (
            f"{SCRIPT_DIR}/../output_ensembles/GN/r_units_{num_r_units}_map_{map_number}/block_size_{block_size}/"
            f"sample_{sample}/init_part_{init_part}_random_seed_{random_seed}_burst_length_20_steps_{total_steps}_assignment.ben"
        )
        save_updaters_results_to = (
            f"{SCRIPT_DIR}/../output_stats/GN/r_units_{num_r_units}_map_{map_number}/block_size_{block_size}/"
            f"sample_{sample}/init_part_{init_part}_random_seed_{random_seed}_burst_length_20_steps_{total_steps}_updaters.jsonl"
        )
        os.makedirs(os.path.dirname(save_assignment_results_to), exist_ok=True)
        os.makedirs(os.path.dirname(save_updaters_results_to), exist_ok=True)

        # Load building block graph
        block_data = (
            f"{SCRIPT_DIR}/syn_building_block_partitions/gerry/"
            f"r_units_{num_r_units}_map_{map_number}_burst_length_20/block_size_{block_size}/sample_{sample}.json"
        )

        block_graph = Graph.from_json(block_data)

        # For use later when saving results
        graph_node_order = list(block_graph.nodes)
    
        # Updaters
        my_updaters = {
            "population": updaters.Tally("population",alias="population"),
            "election": Election("election", {"D": "D", "R": "R"}),
            "R_tally": updaters.Tally("R",alias="R_tally"),
            "D_tally": updaters.Tally("D",alias="D_tally"),
            }

        # Pull initial partition for block graph
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

        # Define recom chain; note using neutral MarkovChain
        recom_chain = MarkovChain(
            proposal=proposal,
            constraints=[contiguous],
            initial_state=initial_partition,
            accept=always_accept,
            total_steps=total_steps
        )

        # Save results
        with (
                PyBenEncoder(save_assignment_results_to, overwrite=True) as encoder,
                jl.open(save_updaters_results_to, "w") as updater_output_file,
            ):
        
            for i, plan in enumerate(recom_chain):

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