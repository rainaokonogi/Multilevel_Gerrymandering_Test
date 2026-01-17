#!/usr/bin/env bash

echo "started"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

for block_set in "gerry" "neutral"; do
    echo "Running with block_set=$block_set"

    SCRIPT="${TOP_DIR}/block_builder_${block_set}.py"

    sbatch --job-name="${block_set}-building-blocks" \
        --nodes=1 \
        --ntasks=1 \
        --partition=duchin \
        --cpus-per-task=2 \
        --mem=2G \
        --time=1-00:00:00 \
        --error="building_blocks_${block_set}.log" \
        --output="building_blocks_${block_set}.out" \
        --wrap="PYTHONHASHSEED=0 uv run $SCRIPT"
done