#!/bin/bash
#SBATCH --job-name=BTReport
#SBATCH --partition=gpu-a40
#SBATCH --account=kurtlab
#SBATCH --array=0-5
#SBATCH --gpus-per-node=a40:2
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH --time=48:00:00
#SBATCH --chdir=/gscratch/scrubbed/juampablo/BTReportEval/BTReport
#SBATCH --output=logs/%A/btreport-%A_%a.out
#SBATCH --error=logs/%A/btreport-%A_%a.err


echo "=========================================="
echo "Job ID        : $SLURM_JOB_ID"
echo "Array Task ID : $SLURM_ARRAY_TASK_ID"
echo "Node          : $(hostname)"
echo "CUDA_VISIBLE_DEVICES=$CUDA_VISIBLE_DEVICES"
echo "Working dir   : $(pwd)"
echo "=========================================="


source ~/.bashrc
source docs/btreport_paths.sh


module load apptainer
conda activate BTReport

# Start ollama server
tmux new -d -s ollama_server \
  "python3 -m btreport.ollama_server start-ollama --gpus 0,1"

# Give the server a moment to come up
sleep 15

# Optional: sanity check
tmux has-session -t ollama_server || {
  echo "ERROR: Ollama tmux session failed to start"
  exit 1
}

export PYTHONUNBUFFERED=1
python3 -m btreport.run_all_reports \
  --root_folder data \
  --num_splits 6 \
  --split_no ${SLURM_ARRAY_TASK_ID} 
  # --llm llama3:70b

echo "Array task ${SLURM_ARRAY_TASK_ID} finished."
