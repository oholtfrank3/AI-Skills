"""Tests for scripts/check_qchem_input.py (stdlib only).

Run: python3 -m unittest discover -s tests -v
"""
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "check_qchem_input.py")

MOL = "$molecule\n0 1\nAr 0.0 0.0 0.0\nAr 0.0 0.0 3.5\n$end\n"
CAP_BLOCK = ("$complex_ccman\nCS_HF 1\nCAP_ETA 500  ! 0.005 a.u.\n"
             "CAP_X 6000\nCAP_Y 6000\nCAP_Z 8000\nCAP_TYPE 1\n$end\n")


def rem(*lines):
    return "$rem\n" + "".join(l + "\n" for l in lines) + "$end\n"


def check(text):
    """Run the checker on one input; return (exit code, stdout)."""
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "job.in")
        with open(path, "w") as f:
            f.write(text)
        p = subprocess.run([sys.executable, SCRIPT, path], capture_output=True, text=True)
    return p.returncode, p.stdout


GOOD_CAP_REM = rem("METHOD EOM-CCSD", "BASIS aug-cc-pVDZ", "COMPLEX_CCMAN 1", "IP_STATES [1]",
                   "SYMMETRY false", "SYM_IGNORE TRUE", "CC_SYMMETRY false",
                   "EOM_DAVIDSON_CONVERGENCE 7")


class ComplexCcmanBlock(unittest.TestCase):
    def test_missing_block_is_error(self):
        code, out = check(MOL + GOOD_CAP_REM)
        self.assertEqual(code, 1, out)
        self.assertIn("no $complex_ccman block", out)
        self.assertIn("eom-cc §5a", out)

    def test_clean_cap_input_passes(self):
        code, out = check(MOL + GOOD_CAP_REM + CAP_BLOCK)
        self.assertEqual(code, 0, out)
        self.assertIn("OK", out)

    def test_fno_with_complex_ccman_is_error(self):
        text = MOL + GOOD_CAP_REM.replace("$end", "CC_FNO_THRESH 9900\n$end") + CAP_BLOCK
        code, out = check(text)
        self.assertEqual(code, 1, out)
        self.assertIn("hf/c_o1b", out)

    def test_cap_keys_in_block_count_as_cap(self):
        # CAP parameters live in $complex_ccman; loose Davidson must still be caught.
        text = MOL + GOOD_CAP_REM.replace("EOM_DAVIDSON_CONVERGENCE 7\n", "") + CAP_BLOCK
        code, out = check(text)
        self.assertEqual(code, 1, out)
        self.assertIn("EOM_DAVIDSON_CONVERGENCE", out)


class CapOrientation(unittest.TestCase):
    def test_box_without_frame_lock_warns(self):
        text = MOL + rem("METHOD EOM-CCSD", "BASIS aug-cc-pVDZ", "COMPLEX_CCMAN 1", "IP_STATES [1]",
                         "EOM_DAVIDSON_CONVERGENCE 7") + CAP_BLOCK
        code, out = check(text)
        self.assertEqual(code, 0, out)
        self.assertIn("WARN", out)
        self.assertIn("reorienting", out)

    def test_voronoi_cap_does_not_warn(self):
        block = CAP_BLOCK.replace("CAP_TYPE 1", "CAP_TYPE 2")
        text = MOL + rem("METHOD EOM-CCSD", "BASIS aug-cc-pVDZ", "COMPLEX_CCMAN 1", "IP_STATES [1]",
                         "EOM_DAVIDSON_CONVERGENCE 7") + block
        _, out = check(text)
        self.assertNotIn("reorienting", out)


class ProjectedCap(unittest.TestCase):
    PROJ = "$complex_ccman\nPROJ_CAP 3\n$end\n"

    def test_no_cc_trans_prop_warning(self):
        # The group's working PROJ_CAP 3 + GUI 2 runs had no CC_TRANS_PROP (manual 6.3 p. 583).
        text = MOL + GOOD_CAP_REM.replace("$end", "GUI 2\n$end") + self.PROJ
        code, out = check(text)
        self.assertEqual(code, 0, out)
        self.assertNotIn("CC_TRANS_PROP", out)

    def test_missing_gui_is_info(self):
        code, out = check(MOL + GOOD_CAP_REM + self.PROJ)
        self.assertEqual(code, 0, out)
        self.assertIn("INFO", out)
        self.assertIn("GUI = 2", out)

    def test_user_guess_with_projected_cap_warns(self):
        text = MOL + GOOD_CAP_REM.replace("$end", "GUI 2\nEOM_USER_GUESS 1\n$end") + self.PROJ
        _, out = check(text)
        self.assertIn("EOM_SHIFT", out)


class OtherTraps(unittest.TestCase):
    def test_user_guess_with_dip_warns(self):
        text = MOL + rem("METHOD EOM-CCSD", "BASIS aug-cc-pVDZ", "DIP_SINGLETS [2]", "EOM_USER_GUESS 1")
        code, out = check(text)
        self.assertEqual(code, 0, out)
        self.assertIn("double free", out)

    def test_cc_frozen_core_is_error(self):
        text = MOL + rem("METHOD EOM-CCSD", "BASIS aug-cc-pVDZ", "IP_STATES [2]", "CC_FROZEN_CORE 5")
        code, out = check(text)
        self.assertEqual(code, 1, out)
        self.assertIn("N_FROZEN_CORE", out)

    def test_inline_comments_in_rem_are_ignored(self):
        text = MOL + rem("METHOD EOM-CCSD ! method", "BASIS aug-cc-pVDZ", "IP_STATES [2]",
                         "! a whole-line comment", "N_FROZEN_CORE FC")
        code, out = check(text)
        self.assertEqual(code, 0, out)
        self.assertIn("OK", out)


if __name__ == "__main__":
    unittest.main()
