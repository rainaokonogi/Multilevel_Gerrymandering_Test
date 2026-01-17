#!/usr/bin/env bash
echo "started"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

for block_set in "gerry" "neutral"; do
    echo "Running with block_set=$block_set"

    SCRIPT="${TOP_DIR}/block_builder_${block_set}.py"

    PYTHONHASHSEED=0 uv run "$SCRIPT"
done