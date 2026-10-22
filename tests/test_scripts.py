"""Smoke tests for the plugin's scripts and safety hook (stdlib only).

Run: python3 -m unittest discover -s tests -v
"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(script, *args, stdin=None):
    p = subprocess.run([sys.executable, os.path.join(ROOT, script), *args],
                       input=stdin, capture_output=True, text=True)
    return p.returncode, p.stdout


def write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w") as f:
        f.write(text)
    return path


class SlurmGuard(unittest.TestCase):
    def decision(self, cmd):
        _, out = run("hooks/slurm_guard.py",
                     stdin=json.dumps({"tool_name": "Bash", "tool_input": {"command": cmd}}))
        return json.loads(out)["hookSpecificOutput"]["permissionDecision"] if out.strip() else None

    def test_asks_for_risky(self):
        for cmd in ["sbatch job.sh", "cd run && sbatch -p inferno x.sh", "scancel 123",
                    "scontrol update JobId=1 TimeLimit=2:00:00", "scontrol hold 5"]:
            self.assertEqual(self.decision(cmd), "ask", cmd)

    def test_passes_read_only(self):
        for cmd in ["squeue -u $USER", "sacct -j 1", "sbatch --test-only job.sh",
                    "scontrol show job 1", "cat my_sbatch_notes.txt", "ls sbatch-scripts/"]:
            self.assertIsNone(self.decision(cmd), cmd)


class QchemOutput(unittest.TestCase):
    def test_unfinished_job_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run("scripts/check_qchem_output.py", write(tmp, "a.out", "SCF energy\n"))
        self.assertEqual(code, 1)
        self.assertIn("Thank you very much", out)

    def test_satellite_and_missing_roots(self):
        text = ("IP_STATES = [3]\n"
                " EOMIP-CCSD transition 1/A\n  Excitation energy = 12.60 eV\n  R1^2 = 0.95 Res^2 = 1e-6\n"
                " EOMIP-CCSD transition 2/A\n  Excitation energy = 30.10 eV\n  R1^2 = 0.30 Res^2 = 1e-6\n"
                " Thank you very much for using Q-Chem.\n")
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run("scripts/check_qchem_output.py", write(tmp, "b.out", text))
        self.assertEqual(code, 0)
        self.assertIn("2 EOM roots printed, 3 requested", out)
        self.assertIn("satellites", out)


class SharcLis(unittest.TestCase):
    def lis(self, etots):
        rows = ["# header"] + [f"{i} {i * 0.5:.2f} 2 2 0.500 -1.0 {e:.6f} 0.1 0.0 0.0 1.0"
                                for i, e in enumerate(etots)]
        return "\n".join(rows) + "\n"

    def test_conserved(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run("scripts/check_sharc_lis.py", write(tmp, "ok.lis", self.lis([-1.0] * 20)))
        self.assertEqual(code, 0)
        self.assertIn("OK", out)

    def test_large_drift_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run("scripts/check_sharc_lis.py",
                            write(tmp, "bad.lis", self.lis([-1.0 + 0.01 * i for i in range(20)])))
        self.assertEqual(code, 1)
        self.assertIn("ERROR", out)


class InputCheckers(unittest.TestCase):
    def test_run_on_minimal_files(self):
        qin = "$molecule\n0 1\nHe 0 0 0\n$end\n$rem\nMETHOD HF\nBASIS cc-pVDZ\n$end\n"
        sb = "#!/bin/bash\n#SBATCH -A acct\n#SBATCH -q inferno\n#SBATCH -t 1:00:00\n#SBATCH --mem=8G\necho hi\n"
        with tempfile.TemporaryDirectory() as tmp:
            for script, name, text in [("scripts/check_qchem_input.py", "he.in", qin),
                                       ("scripts/check_sbatch.py", "job.sbatch", sb)]:
                code, out = run(script, write(tmp, name, text))
                self.assertIn(code, (0, 1), out)
                self.assertNotIn("Traceback", out)


if __name__ == "__main__":
    unittest.main()
