#!/bin/bash 
#SBATCH --job-name=add-init-parts
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --partition=duchin
#SBATCH --cpus-per-task=2
#SBATCH --mem=4G
#SBATCH --time=7-00:00:00
#SBATCH --error=init_parts_error.log
#SBATCH --output=init_parts_output.out

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOP_DIR="$(realpath "${SCRIPT_DIR}/..")"

SCRIPT="${TOP_DIR}/add_init_parts_to_gerry_blocks.py"

PYTHONHASHSEED=0 uv run $SCRIPT