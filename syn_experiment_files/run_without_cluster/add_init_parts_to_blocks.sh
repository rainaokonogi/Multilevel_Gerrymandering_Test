#!/usr/bin/env bash

echo "started"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

for block_set in "gerry" "neutral"; do
    echo "Running with block_set=$block_set"

    SCRIPT="${TOP_DIR}/add_init_parts_to_${block_set}_blocks.py"

    PYTHONHASHSEED=0 uv run "$SCRIPT"
done