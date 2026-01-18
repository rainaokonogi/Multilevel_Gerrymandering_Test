#!/usr/bin/env bash

echo "started"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

for block_type in "blockgroups" "vtds" "tracts"; do
    echo "Running with block_type=$block_type, random_seed=$random_seed"
    PYTHONHASHSEED=0 uv run "${TOP_DIR}/add_init_parts_to_dual_graphs_cli.py --block-type $block_type"
done