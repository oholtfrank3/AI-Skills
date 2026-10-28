#!/bin/bash
#SBATCH -J h3o_aimd                  # job name
#SBATCH -A <your-account>            # PACE charge account (see pace-slurm skill)
#SBATCH -N 1 --ntasks-per-node=24    # one node, 24 MPI ranks
#SBATCH --mem-per-cpu=1G             # 24 GB total is plenty for 190 atoms
#SBATCH -t 01:00:00                  # WALLTIME in water.inp stops CP2K at 30 min, cleanly
#SBATCH -o slurm-%j.out              # Slurm log; CP2K writes its own WATER.out

cd $SLURM_SUBMIT_DIR                 # run where the inputs are

module load gcc openmpi cp2k         # check `module spider cp2k` for the current version

# CP2K finds HFX_BASIS, POTENTIAL and dftd3.dat here; the module usually sets it.
# If CP2K stops with "file not found", point this at the module's data/ folder.
# export CP2K_DATA_DIR=<cp2k install>/data

srun -n 24 cp2k.psmp -i water.inp -o WATER.out   # cp2k.popt on older builds
