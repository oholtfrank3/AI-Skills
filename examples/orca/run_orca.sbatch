#!/bin/bash
# ORCA on PACE Phoenix: template, NOT tested on PACE yet (orca skill §2).
# ORCA uses MPI processes: --ntasks must equal %pal nprocs in the input; keep -c 1.
# %maxcore (MB per process) ~75 % of --mem-per-cpu: 4G per task -> %maxcore 3000.
# Partition routing for --ntasks jobs is unverified: check with sbatch --test-only first.
# Usage: sbatch -J water_dlpno_ccsdt run_orca.sbatch   (job name = input name without .inp)
#SBATCH -A <your-account>          # PACE charge account (pace-slurm skill)
#SBATCH -q inferno                 # inferno = paid, not preempted; embers = free, preemptible
#SBATCH -N 1                       # ORCA's MPI runs on one node here
#SBATCH --ntasks=4                 # = %pal nprocs in the input
#SBATCH --cpus-per-task=1          # one core per MPI process; more would sit idle
#SBATCH --mem-per-cpu=4G           # %maxcore 3000 leaves ~25 % headroom
#SBATCH -t 1:00:00                 # water DLPNO-CCSD(T) needs minutes; 2-3x measured for real jobs
#SBATCH -o slurm-%j.out            # Slurm log; ORCA output goes to $job.out
#SBATCH -e slurm-%j.err            # Slurm errors

set -euo pipefail
job=$SLURM_JOB_NAME

# Fill in after installing ORCA and the matching OpenMPI (or after `module load ...` if PACE has one).
ORCADIR=/path/to/orca_6_1_1
MPIDIR=/path/to/openmpi-4.1.6
export PATH=$ORCADIR:$MPIDIR/bin:$PATH
export LD_LIBRARY_PATH=$ORCADIR:$MPIDIR/lib:${LD_LIBRARY_PATH:-}
which mpirun

# Node-local scratch, one directory per job.
work=$TMPDIR/orca_$SLURM_JOB_ID
mkdir -p "$work"
cp "$SLURM_SUBMIT_DIR/$job.inp" "$work/"
cd "$work"

# Full path, no mpirun/srun: ORCA starts its own MPI processes.
"$ORCADIR/orca" "$job.inp" > "$SLURM_SUBMIT_DIR/$job.out" || status=$?

# Copy back what exists, even after a failure.
for ext in gbw xyz hess engrad; do
  if [ -e "$job.$ext" ]; then cp "$job.$ext" "$SLURM_SUBMIT_DIR/"; fi
done
# A clean run ends with ****ORCA TERMINATED NORMALLY****
if grep -q "ORCA TERMINATED NORMALLY" "$SLURM_SUBMIT_DIR/$job.out"; then echo "finished normally"; fi
exit ${status:-0}
