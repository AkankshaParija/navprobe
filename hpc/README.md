# Running NavProbe models on a Slurm GPU cluster

Only the model-querying step needs a GPU. Generation, verification and the report run on a laptop.

## 1. Copy the project (from your Mac)
```bash
rsync -avP --exclude .git ./ USER@LOGIN-NODE:~/navprobe/
```

## 2. One-time environment (on the login node)
The cluster module is Python 3.13; the laptop pins (numpy 1.26 / Pillow 10.3) have no 3.13 wheels and are
not needed on the HPC (it only sends existing PNGs to models). /home has a 10 GB quota and a vLLM env is
~10 GB, so the env, uv cache and weights all live in /scratch (rebuild in ~5 min if scratch is purged):
```bash
export S=/scratch/$USER
mkdir -p $S/hf $S/envs ~/navprobe/logs
module load python
python3 -m pip install --target $S/uvpkg uv
export UV_CACHE_DIR=$S/uv-cache UV_PYTHON_INSTALL_DIR=$S/uv-python
$S/uvpkg/bin/uv venv $S/envs/navprobe --python 3.12
source $S/envs/navprobe/bin/activate
$S/uvpkg/bin/uv pip install vllm transformers accelerate qwen-vl-utils requests pillow numpy scipy matplotlib huggingface_hub
```
vLLM ships its own CUDA PyTorch build, so this env does not use the cluster's PyTorch module.
Test it in a short GPU session before the real runs:
```bash
srun --partition=rtx --gres=gpu:1g.24gb:1 --cpus-per-task=8 --mem=32G --time=00:20:00 --pty bash
source ~/envs/navprobe/bin/activate && cd ~/navprobe
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
HF_HOME=/scratch/$USER/hf python -m navprobe.evaluate --tasks outputs --model vllm:Qwen/Qwen2.5-VL-3B-Instruct --limit 20
```
If vLLM fails, use `BACKEND=hf` (transformers), which is slower but simpler.

Compute nodes have NO internet (checked 24 Nov: curl exit code 6), so always download weights on the login node first:
```bash
HF_HOME=/scratch/$USER/hf huggingface-cli download Qwen/Qwen2.5-VL-7B-Instruct
```

## 3. Submit the runs (one job per model)
```bash
cd ~/navprobe
sbatch --export=ALL,MODEL=Qwen/Qwen2.5-VL-3B-Instruct hpc/run_model.sbatch
sbatch --export=ALL,MODEL=Qwen/Qwen2.5-VL-7B-Instruct hpc/run_model.sbatch
sbatch --gres=gpu:2g.48gb:1 --export=ALL,MODEL=Qwen/Qwen2.5-VL-32B-Instruct-AWQ hpc/run_model.sbatch
squeue -u $USER
```
The course QOS allows 2 jobs at once, so submit 2, wait, then submit the rest.

## 4. Bring results back (from your Mac)
```bash
rsync -avP USER@LOGIN-NODE:~/navprobe/outputs/responses/ ./outputs/responses/
cd ~/Desktop/INTERNSHIPS/hackathon/navprobe && make report
```
