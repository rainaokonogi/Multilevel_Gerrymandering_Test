#!/usr/bin/env bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

echo "started"
for random_seed in {1..5}; do
    for init_part in {1..5}; do
        for election in "pres" "sen"; do
            for party in "D" "R"; do
                for block_type in "blockgroups" "vtds" "tracts"; do

                    echo "Running with block_type=$block_type, election=$election, party=$party, init_part=$init_part, and random_seed=$random_seed"
                    
                    sbatch --job-name="NY-gerry-exps" \
                        --nodes=1 \
                        --ntasks=1 \
                        --partition=duchin \
                        --cpus-per-task=2 \
                        --mem=2G \
                        --time=4-00:00:00 \
                        --error="NY_error_files/NY_gerry_exps_${block_type}_${election}_${party}_part_${init_part}_seed_${random_seed}.log" \
                        --output="NY_output_files/NY_gerry_exps_${block_type}_${election}_${party}_part_${init_part}_seed_${random_seed}.out" \
                        --wrap="PYTHONHASHSEED=0 uv run ${TOP_DIR}/NY_gerry_exps_cli.py --block-type $block_type --election $election --party $party --init-part $init_part --random-seed $random_seed --total-steps 1000000"
                done
            done
        done
    done
done