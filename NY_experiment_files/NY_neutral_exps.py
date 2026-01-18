from gerrychain import Partition, Graph, accept, MarkovChain, updaters, Election
from gerrychain.proposals import recom
from gerrychain.tree import bipartition_tree
from gerrychain.constraints import contiguous
from gerrychain.accept import always_accept
from functools import partial
import random
import jsonlines as jl
import os
from pyben import PyBenEncoder
import json

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

# Block_type indicates whether using block groups, VTDs, or tracts as underlying blocks
# Election/party indicate what data we're using to do the gerrymandering
def NY_gerry_exp(block_type, election, party, init_part, random_seed, total_steps):
    """Runs 

    Args:
        block_type (str): choice of pieces being aggregated into districts (block groups, VTDs, or tracts)
        election (str): data
        party (str): ("D" or "R")
        init_part (int): Number of initial district partition to use for Markov chain (1–5)
        random_seed (int): Random seed for reproducibility.
        total_steps (int): Total number of steps for each chain.
    """

    # Load dual graph
    dual_graph_info = (
        f"{SCRIPT_DIR}/NY_dual_graphs/connected_dual_graphs_with_initial_partitions/
        conn_{block_type}_dual_graph_init_parts.json"
    )

    dual_graph = Graph.from_json(dual_graph_info)

    # For use later when saving results
    graph_node_order = list(dual_graph.nodes)

    save_assignment_results_to = f"{SCRIPT_DIR}/../NY_output_ensembles/{block_type}/neutral/
                                init_part_{init_part}_random_seed_{random_seed}_burst_length_20_{total_steps}_steps_assignment.ben"
    save_updaters_results_to = f"{SCRIPT_DIR}/../NY_output_ensembles/{block_type}/neutral/
                                init_part_{init_part}_random_seed_{random_seed}_burst_length_20_{total_steps}_steps_updaters.jsonl"
    os.makedirs(os.path.dirname(save_assignment_results_to), exist_ok=True)
    os.makedirs(os.path.dirname(save_updaters_results_to), exist_ok=True)

    # Set pop data, random seed
    pop_col = "TOT_POP"
    random.seed(random_seed)

    # Define updaters
    # Only tracking vote totals for Gingleator, so define different updaters depending on whether we're gerrymandering on Pres vs. Sen election data
    if election == "pres":
        my_updaters = {
            "population": updaters.Tally(pop_col, alias="population"),
            "pres_election": Election(
                "pres_election", {"D": "PRES20DEM", "R": "PRES20REP"}
            ),
            "sen_election": Election(
                "sen_election", {"D": "SEN22DEM", "R": "SEN22REP"}
            ),
            "D_vote_population": updaters.Tally("PRES20DEM", alias="D_vote_population"),
            "R_vote_population": updaters.Tally("PRES20REP", alias="R_vote_population"),
            "total_vote_population": updaters.Tally(
                ["PRES20DEM", "PRES20REP"], alias="total_vote_population"
            ),
        }

    elif election == "sen":
        my_updaters = {
            "population": updaters.Tally(pop_col, alias="population"),
            "pres_election": Election(
                "pres_election", {"D": "PRES20DEM", "R": "PRES20REP"}
            ),
            "sen_election": Election(
                "sen_election", {"D": "SEN22DEM", "R": "SEN22REP"}
            ),
            "D_vote_population": updaters.Tally("SEN22DEM", alias="D_vote_population"),
            "R_vote_population": updaters.Tally("SEN22REP", alias="R_vote_population"),
            "total_vote_population": updaters.Tally(
                ["SEN22DEM", "SEN22REP"], alias="total_vote_population"
            ),
        }

    initial_partition = Partition(
        dual_graph,
        assignment=f"init_part_{init_part}",
        updaters=my_updaters
    )

    # Define proposal
    # Note: total pop is 20,201,249, hence rounded pop target for 63 districts is 320,655
    proposal = partial(
        recom,
        pop_col=pop_col,
        pop_target=320655,
        epsilon=0.01,
        node_repeats=2,
        method=partial(bipartition_tree, allow_pair_reselection=True),
    )

    # Define recom chain
    recom_chain = MarkovChain(
        proposal=proposal,
        constraints=[contiguous],
        initial_state=initial_partition,
        accept=always_accept,
        total_steps=total_steps
    )

    # Save assignments, updater results
    with (
        PyBenEncoder(save_assignment_results_to, overwrite=True) as encoder,
        jl.open(save_updaters_results_to, "w") as updater_output_file
    ):
        for i, plan in enumerate(recom_chain):
            if i % 100 == 0:
                print(f"Processing plan {i}...")

            assert (
                plan is not None
            ), "Something went terribly wrong. There is no output partition."

            # Save updaters
            pres_election = plan["pres_election"]
            sen_election = plan["sen_election"]

            pres_seats_won = {
                "D": pres_election.seats("D"),
                "R": pres_election.seats("R"),
            }

            sen_seats_won = {
                "D": sen_election.seats("D"),
                "R": sen_election.seats("R"),
            }

            pres_regions = pres_election.regions
            sen_regions = sen_election.regions

            pres_d_counts = pres_election.counts("D")
            pres_r_counts = pres_election.counts("R")
            pres_d_votes_by_district = dict(zip(pres_regions, pres_d_counts))
            pres_r_votes_by_district = dict(zip(pres_regions, pres_r_counts))

            sen_d_counts = sen_election.counts("D")
            sen_r_counts = sen_election.counts("R")
            sen_d_votes_by_district = dict(zip(sen_regions, sen_d_counts))
            sen_r_votes_by_district = dict(zip(sen_regions, sen_r_counts))

            pres_district_winners = {region: ("D" if d > r else "R") for region, d, r in zip(pres_regions, pres_d_counts, pres_r_counts)}
            sen_district_winners = {region: ("D" if d > r else "R") for region, d, r in zip(sen_regions, sen_d_counts, sen_r_counts)}

            record = {
                "sample": i + 1,
                "population": dict(plan["population"]),
                "Pres seats won": pres_seats_won,
                "Pres D votes": pres_d_votes_by_district,
                "Pres R votes": pres_r_votes_by_district,
                "Sen seats won": sen_seats_won,
                "Sen D votes": sen_d_votes_by_district,
                "Sen R votes": sen_r_votes_by_district,
                "District Pres seats": pres_district_winners,
                "District Sen seats": sen_district_winners
            }

            updater_output_file.write(record)