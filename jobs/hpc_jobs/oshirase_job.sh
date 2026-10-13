#!/bin/bash
# Generic outer sbatch entry point. This meta-job just submits the real work via
# submitit (from inside the target Python script) and then blocks, polling until
# it's done, before Slack-notifying -- so its own resource footprint is always
# this same lightweight "submit + poll + notify" shape regardless of which
# pipeline/job script it launches.
#
# Usage (run from inside jobs/hpc_jobs/, since job scripts use folder="../.submitit"):
#   sbatch _run_wrapper.sh run_pm.py
#   sbatch _run_wrapper.sh run_pm_holo_ai228.py
#
# To override resources/partition/mail for a one-off job without a new file:
#   sbatch --partition=gpu_lowp --mail-user=you@example.com _run_wrapper.sh run_pm.py

#SBATCH --job-name=submitit
#SBATCH --cpus-per-task=1
#SBATCH --ntasks=1
#SBATCH --time=72:00:00
#SBATCH --mem=4G
#SBATCH --mail-type=BEGIN,END,FAIL
#SBATCH --mail-user=s.kuroda@ucl.ac.uk

# Not every node has this file (e.g. enc1-*); `module` may still be inherited
# from the submitting shell, so don't fail here.
if [ -f /etc/profile.d/modules.sh ]; then
  source /etc/profile.d/modules.sh
fi
echo "SLURM job info:"
scontrol show job $SLURM_JOB_ID

export PYTHONUNBUFFERED=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

module load miniconda
# `conda activate` only works once conda's shell hook is loaded, which a
# non-interactive batch shell doesn't do on its own.
eval "$(conda shell.bash hook)"
conda activate photon-mosaic-pipeline
echo "Using python: $(which python)"
if ! python -c "import oshirase" 2>/dev/null; then
  echo "ERROR: oshirase not importable from $(which python); is photon-mosaic-pipeline activated?" >&2
  exit 1
fi

if [ -z "$1" ]; then
  echo "Usage: sbatch _run_wrapper.sh <script.py> [extra python args...]" >&2
  exit 1
fi

SCRIPT="$1"; shift
srun python "$SCRIPT" "$@"
