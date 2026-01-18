#!/bin/bash

#!/usr/bin/env bash

echo "started"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

for block_type in "blockgroups" "vtds" "tracts"; do
    echo "Running with block_type=$block_type"

    sbatch --job-name="${block_type}-init-parts" \
        --nodes=1 \
        --ntasks=1 \
        --partition=duchin \
        --cpus-per-task=2 \
        --mem=2G \
        --time=2-00:00:00 \
        --error="init_parts_${block_type}.log" \
        --output="init_parts_${block_type}.out" \
        --wrap="PYTHONHASHSEED=0 uv run ${TOP_DIR}/add_init_parts_to_dual_graphs_cli.py --block-type $block_type"
done