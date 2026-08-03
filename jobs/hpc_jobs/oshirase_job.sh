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

source /etc/profile.d/modules.sh
echo "SLURM job info:"
scontrol show job $SLURM_JOB_ID

export PYTHONUNBUFFERED=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

module load miniconda
conda activate photon-mosaic-pipeline

if [ -z "$1" ]; then
  echo "Usage: sbatch _run_wrapper.sh <script.py> [extra python args...]" >&2
  exit 1
fi

SCRIPT="$1"; shift
srun python "$SCRIPT" "$@"
