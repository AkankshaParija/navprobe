#!/bin/bash
# Submit one Slurm job per model in hpc/models.txt.
# GPU jobs are limited to 1 per QOS, so jobs alternate between the course and general
# QOS and Slurm queues the rest. Each job is resumable.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p logs
i=0
grep -v '^#' hpc/models.txt | awk 'NF' | while read -r model gres; do
  if [ $((i % 2)) -eq 0 ]; then acct=(--account=courses --qos=course); else acct=(--account=general --qos=general); fi
  name="np-$(basename "$model" | cut -c1-20)"
  sbatch "${acct[@]}" --job-name="$name" --gres="$gres" --export=ALL,MODEL="$model" hpc/run_model.sbatch
  i=$((i + 1))
done
squeue -u "$USER"
