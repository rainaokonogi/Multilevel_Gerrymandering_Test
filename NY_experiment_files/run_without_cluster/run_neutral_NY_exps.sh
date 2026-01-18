#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

echo "started"
for random_seed in {1..5}; do
    for init_part in {1..5}; do
        for block_type in "blockgroups" "vtds" "tracts"; do

                    echo "Running with block_type=$block_type, init_part=$init_part, and random_seed=$random_seed"
                    
                    PYTHONHASHSEED=0 uv run "${TOP_DIR}/NY_neutral_exps_cli.py --block-type $block_type --init-part $init_part --random-seed $random_seed --total-steps 1000000"
        done
    done
done