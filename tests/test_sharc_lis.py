"""Tests for scripts/check_sharc_lis.py, including '****' energy overflow (stdlib only).

Run: python3 -m unittest discover -s tests -v
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "check_sharc_lis.py")


def run(*args):
    p = subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True)
    return p.returncode, p.stdout


def write(tmp, name, text):
    path = os.path.join(tmp, name)
    with open(path, "w") as f:
        f.write(text)
    return path


def lis(epot_etot):
    rows = ["# Step  Time  State(diag)  State(MCH)  Ekin  Epot  Etot  Grad  Dipole  Spin  Walltime"]
    for i, (ep, et) in enumerate(epot_etot):
        rows.append(f"{i} {i * 0.5:.2f} 2 2 0.500 {ep} {et} 0.1 0.0 0.0 1.0")
    return "\n".join(rows) + "\n"


class SharcLisOverflow(unittest.TestCase):
    def test_all_rows_overflow_warns_without_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run(write(tmp, "ovf.lis", lis([("**********", "**********")] * 10)))
        self.assertEqual(code, 0, out)
        self.assertIn("WARN", out)
        self.assertIn("****", out)
        self.assertIn("output.dat", out)
        self.assertIn("10 step(s)", out)
        self.assertNotIn("fewer than 2 time steps", out)
        self.assertNotIn("Traceback", out)

    def test_partial_overflow_counts_and_still_checks_rest(self):
        rows = [("-1.0", "-0.500000")] * 10 + [("-1.0", "***********")] * 3
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run(write(tmp, "part.lis", lis(rows)))
        self.assertEqual(code, 0, out)
        self.assertIn("3 step(s)", out)
        self.assertIn("10 steps", out)
        self.assertNotIn("OK (energy conserved", out)

    def test_overflow_in_epot_only(self):
        rows = [("********", "-0.500000")] * 5
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run(write(tmp, "epot.lis", lis(rows)))
        self.assertIn("5 step(s)", out)
        self.assertNotIn("Traceback", out)

    def test_clean_file_has_no_overflow_warning(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run(write(tmp, "ok.lis", lis([("-1.0", "-0.500000")] * 20)))
        self.assertEqual(code, 0, out)
        self.assertIn("OK", out)
        self.assertNotIn("****", out)

    def test_too_few_rows_without_overflow_is_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            code, out = run(write(tmp, "short.lis", lis([("-1.0", "-0.5")])))
        self.assertEqual(code, 1)
        self.assertIn("fewer than 2 time steps", out)


if __name__ == "__main__":
    unittest.main()
