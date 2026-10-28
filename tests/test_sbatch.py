"""Tests for scripts/check_sbatch.py (stdlib only).

Run: python3 -m unittest discover -s tests -v
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

HEADER = ("#!/bin/bash\n#SBATCH -A acct\n#SBATCH -q inferno\n#SBATCH -t 12:00:00\n"
          "#SBATCH -c 24 --mem=360G --tmp=1350G --constraint=localNVMe\n")
SCRATCH = "export QCSCRATCH=/tmp/$USER/$SLURM_JOB_ID\nmkdir -p $QCSCRATCH\n"


def check(text):
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "job.sbatch")
        with open(path, "w") as f:
            f.write(text)
        p = subprocess.run([sys.executable, os.path.join(ROOT, "scripts/check_sbatch.py"), path],
                           capture_output=True, text=True)
    return p.returncode, p.stdout


class Threads(unittest.TestCase):
    def test_nt_above_16_warns(self):
        code, out = check(HEADER + SCRATCH + "qchem -nt 24 job.in job.out\n")
        self.assertEqual(code, 0, out)
        self.assertIn("qchem -nt above 16", out)

    def test_nt_16_is_fine(self):
        _, out = check(HEADER + SCRATCH + "qchem -nt 16 job.in job.out\n")
        self.assertNotIn("-nt above 16", out)
        self.assertNotIn("WARN", out)


class OutputClash(unittest.TestCase):
    def test_same_output_name_warns(self):
        _, out = check(HEADER + "#SBATCH -o output.out -e error.err\n" + SCRATCH
                       + "qchem -nt 16 input.in output.out\n")
        self.assertIn("is also Q-Chem's output file", out)

    def test_long_option_warns(self):
        _, out = check(HEADER + "#SBATCH --output=output.out\n" + SCRATCH
                       + "qchem -nt 16 input.in output.out\n")
        self.assertIn("is also Q-Chem's output file", out)

    def test_different_names_ok(self):
        _, out = check(HEADER + "#SBATCH -o slurm-%j.out\n" + SCRATCH + "qchem -nt 16 input.in output.out\n")
        self.assertNotIn("is also Q-Chem's output file", out)


class SaveWithTrap(unittest.TestCase):
    def test_save_and_trap_warns(self):
        _, out = check(HEADER + SCRATCH + "trap 'rm -rf \"$QCSCRATCH\"' EXIT\n"
                       + "qchem -nt 16 -save job.in job.out savedir\n")
        self.assertIn("-save together with a trap", out)

    def test_trap_without_save_ok(self):
        _, out = check(HEADER + SCRATCH + "trap 'rm -rf \"$QCSCRATCH\"' EXIT\n"
                       + "qchem -nt 16 job.in job.out\n")
        self.assertNotIn("-save together with a trap", out)

    def test_save_without_trap_ok(self):
        _, out = check(HEADER + SCRATCH + "qchem -nt 16 -save job.in job.out savedir\n")
        self.assertNotIn("-save together with a trap", out)


if __name__ == "__main__":
    unittest.main()
