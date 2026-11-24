#!/bin/bash
# Download every model in hpc/models.txt on the LOGIN node (compute nodes have no internet).
# This cluster intermittently fails large writes with "Bad address (os error 14)";
# downloads resume, so each model is retried until it completes.
#
#   bash hpc/download_models.sh            # all models
#   bash hpc/download_models.sh Qwen/Qwen3-VL-8B-Instruct   # just one
set -uo pipefail
source "/scratch/$USER/envs/navprobe/bin/activate"
export HF_HOME="/scratch/$USER/hf" HF_HUB_DISABLE_XET=1

cd "$(dirname "$0")/.."
models=("$@")
if [ ${#models[@]} -eq 0 ]; then
  mapfile -t models < <(grep -v '^#' hpc/models.txt | awk 'NF{print $1}')
fi

for m in "${models[@]}"; do
  for attempt in $(seq 1 20); do
    echo "=== $m (attempt $attempt)"
    if hf download "$m" --max-workers 1 >/dev/null; then
      echo "OK  $m"
      break
    fi
    sleep 5
  done
done
du -sh "$HF_HOME/hub"/models--* 2>/dev/null
