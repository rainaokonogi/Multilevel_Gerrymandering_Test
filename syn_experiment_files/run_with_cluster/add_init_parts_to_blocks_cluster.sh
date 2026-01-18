#!/usr/bin/env bash

echo "started"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

for block_set in "gerry" "neutral"; do
    echo "Running with block_set=$block_set"

    SCRIPT="${TOP_DIR}/add_init_parts_to_${block_set}_blocks.py"

    sbatch --job-name="${block_set}-init-parts" \
        --nodes=1 \
        --ntasks=1 \
        --partition=duchin \
        --cpus-per-task=2 \
        --mem=2G \
        --time=2-00:00:00 \
        --error="init_parts_${block_set}.log" \
        --output="init_parts_${block_set}.out" \
        --wrap="PYTHONHASHSEED=0 uv run $SCRIPT"
done