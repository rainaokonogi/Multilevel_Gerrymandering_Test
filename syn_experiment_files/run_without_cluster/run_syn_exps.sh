#!/usr/bin/env bash
echo "started"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

for random_seed in {1..5}; do
    for init_part in {1..3}; do
        for experiment_type in "GG" "NG" "GN" "NN" "GGopp"; do
            for map_number in {1..3}; do
                for num_r_units in 72 86 58; do
                    for block_size in 2 3 4 6; do
                        echo "Running with num_r_units=$num_r_units, map_number=$map_number, block_size=$block_size, experiment_type=$experiment_type, init_part=$init_part, and random_seed=$random_seed"
                        PYTHONHASHSEED=0 uv run "${TOP_DIR}/syn_exps_cli.py --num-r-units $num_r_units --map-number $map_number --block-size $block_size --experiment-type $experiment_type --init-part $init_part --random-seed $random_seed --total-steps 20000"
                   done
                done
            done
        done
    done
done