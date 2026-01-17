import networkx as nx
import numpy as np
import random
import os
from gerrychain import Graph
import matplotlib.pyplot as plt
import matplotlib
from matplotlib.colors import ListedColormap, BoundaryNorm

SCRIPT_FILE_PATH = os.path.abspath(__file__)
SCRIPT_DIR = os.path.dirname(SCRIPT_FILE_PATH)

def main():
    """Creates grid graphs that will be used in synthetic experiments.

    Each of these is a 12x12 grid where each unit has population 1
    and represents either one Democratic or one Republic vote.

    Creates nine maps total:
    three of these have 58 Republicans and 86 Democrats (approx. a 40% R–60% D split),
    three of these have 72 Republicans and 72 Democrats (a 50%-50% split),
    and three of these have 86 Republicans and 58 Democrats (approx. a 60% R–40% D split).

    Also creates .png images of these maps.
    """
    random_seed = 362
    random.seed(random_seed)
    
    create_blank_grid()

    for num_r_units in [58, 72, 86]:
        for map_number in [1, 2, 3]:
            create_dual_graph(num_r_units, map_number)
            create_dual_graph_image(num_r_units, map_number)

def create_blank_grid():
    unit_dual_graph = Graph.from_networkx(nx.grid_2d_graph(12,12))
    unit_dual_graph = Graph.from_networkx(nx.relabel.convert_node_labels_to_integers(unit_dual_graph, label_attribute ="old_node_index"))
    for unit, data in unit_dual_graph.nodes(data=True):
        data['population'] = 1

    save_grid_to = (
        f"{SCRIPT_DIR}/../syn_unit_maps/"
        f"12x12_grid_no_votes.json"
    )
    os.makedirs(os.path.dirname(save_grid_to), exist_ok=True)
    unit_dual_graph.to_json(save_grid_to)

def create_dual_graph(num_r_units, map_number):
    """Creates .json files for maps described above.

    Args:
        num_r_units: number of Republican votes (58, 72, or 86)
        map_number: sample number out of maps with that partisan split (1, 2, or 3)
    """
    save_grid_maps_to = (
        f"{SCRIPT_DIR}/../syn_unit_maps/map_.jsons/"
        f"r_units_{num_r_units}_map_{map_number}.json"
    )
    os.makedirs(os.path.dirname(save_grid_maps_to), exist_ok=True)
    
    # Create blank 12x12 grid
    unit_dual_graph = Graph.from_networkx(nx.grid_2d_graph(12,12))
    unit_dual_graph = Graph.from_networkx(nx.relabel.convert_node_labels_to_integers(unit_dual_graph, label_attribute ="old_node_index"))

    # Shuffle units in a random order (so as to forget geographic info)
    # Proceed through this order, assigning each unit 0 (representing Republican)
    # until you've hit the desired number of Republican votes.
    # Then assign every remaining unit 1 (representing Democratic)
    units = list(unit_dual_graph.nodes)
    random.shuffle(units)
    unit_partisan_assignments = {}
    d_counter = 0
    r_counter = 0
    for unit in units:
        if r_counter != num_r_units:
            unit_partisan_assignments[unit] = 0
            r_counter = r_counter + 1
        else:
            unit_partisan_assignments[unit] = 1
            d_counter = d_counter + 1

    # Check the right number of units were assigned D/R.
    assert(r_counter == num_r_units), "Something went terribly wrong. Map did not assign correct number of Republican units."
    assert(d_counter == 144-num_r_units), "Something went terribly wrong. Map did not assign correct number of Democratic units."

    # Save population, voter data to graph.
    for unit, data in unit_dual_graph.nodes(data=True):
        data['population'] = 1
        if unit_partisan_assignments[unit] == 1:
            data['D'] = 1
            data['R'] = 0 
        else:    
            data['D'] = 0
            data['R'] = 1

    unit_dual_graph.to_json(save_grid_maps_to)


def create_dual_graph_image(num_r_units, map_number):
    """Creates .png images for maps described above.

    Args:
        num_r_units: number of Republican votes (58, 72, or 86)
        map_number: sample number out of maps with that partisan split (1, 2, or 3)
    """
    save_grid_map_images_to = (
        f"{SCRIPT_DIR}/../syn_unit_maps/map_.pngs/"
        f"r_units_{num_r_units}_map_{map_number}.png"
    )
    os.makedirs(os.path.dirname(save_grid_map_images_to), exist_ok=True)

    # Access appropriate dual graph .json file
    unit_dual_graph_json = (
        f"{SCRIPT_DIR}/../syn_unit_maps/map_.jsons/"
        f"r_units_{num_r_units}_map_{map_number}.json"
    )

    unit_dual_graph = Graph.from_json(unit_dual_graph_json)
    
    # Create a 2D array in which each subarray is one row of the grid graph
    # Each subarray is 12 entries of either 1 (Dem vote) or 0 (Rep vote)
    grid_2D_array = []
    count = 0
    grid_row_array = []
    for unit, data in unit_dual_graph.nodes(data=True):
        if count != 12:
            grid_row_array.append(int(data['D']))
            count = count + 1
            if count == 12:
                grid_2D_array.append(grid_row_array)  
        else:
            count = 0
            grid_row_array = []
            grid_row_array.append(int(data['D']))
            count = 1
        
    # Use 2D array to create image of grid map
    grid_data = grid_2D_array
    cmap = matplotlib.colors.ListedColormap(['red', 'blue'])
    bounds = [0,1]
    norm = matplotlib.colors.BoundaryNorm(bounds, cmap.N)
    fig, ax = plt.subplots()
    ax.imshow(grid_data, cmap=cmap, norm=norm)
    ax.grid(which='major', axis='both', linestyle='-', color='k', linewidth=2)
    ax.set_xticks(np.arange(-0.5, 12, 1))
    ax.set_yticks(np.arange(-0.5, 12, 1))
    ax.set_yticklabels([])
    ax.set_xticklabels([])

    plt.savefig(save_grid_map_images_to)

main()