#!/bin/bash
# Evaluate one model on NavProbe (with image, then blind text-only on base tasks).
# Resumable: rerun the same command after a timeout and it continues where it stopped.
#
#   sbatch --export=ALL,MODEL=Qwen/Qwen2.5-VL-7B-Instruct hpc/run_model.sbatch
#   sbatch --gres=gpu:2g.48gb:1 --export=ALL,MODEL=Qwen/Qwen2.5-VL-32B-Instruct-AWQ hpc/run_model.sbatch
#   BACKEND=hf  -> use transformers instead of vLLM
#
#SBATCH --job-name=navprobe
#SBATCH --partition=rtx
#SBATCH --gres=gpu:1g.24gb:1
#SBATCH --cpus-per-task=8
#SBATCH --mem=32G
#SBATCH --time=00:45:00   # Slurm reserves time-limit x price against the budget up front, so keep this short; reruns resume from cache
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
: "${MODEL:?set MODEL=<huggingface id>}"
BACKEND="${BACKEND:-vllm}"

module load python
source "${VENV:-/scratch/$USER/envs/navprobe}/bin/activate"   # env is ~10 GB: too big for the 10 GB /home quota
export HF_HOME="/scratch/$USER/hf"          # model weights live in scratch (large, purgeable)
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1   # compute nodes have no internet: download on the login node first
cd "${NAVPROBE_DIR:-$HOME/navprobe}"

nvidia-smi -L
python -m navprobe.evaluate --tasks outputs --model "$BACKEND:$MODEL"
python -m navprobe.evaluate --tasks outputs --model "$BACKEND:$MODEL" --blind --base-only
echo "done: responses are in outputs/responses/ (in \$HOME, so they are kept)"
