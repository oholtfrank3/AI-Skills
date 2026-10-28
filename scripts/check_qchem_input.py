#!/usr/bin/env python3
"""Check a Q-Chem input for mistakes that have cost the group jobs.

Usage: python3 check_qchem_input.py job.in [job2.in ...]
Exit code 1 if any ERROR was found, else 0. Each finding cites the skill
section it comes from. Not a full parser: it reads $molecule, $rem, $basis and
$complex_ccman.
"""
import re
import sys


def sections(text):
    """Return {name: [lines]} for every $name ... $end block (first job only)."""
    out, cur = {}, None
    for raw in text.splitlines():
        line = raw.split("!", 1)[0].strip()
        if line.startswith("@@@"):
            break  # multi-job input: check the first job only
        if line.lower().startswith("$end"):
            cur = None
        elif line.startswith("$"):
            cur = line[1:].split()[0].lower()
            out.setdefault(cur, [])
        elif cur is not None and line:
            out[cur].append(line)
    return out


def rem_dict(lines):
    rem = {}
    for line in lines:
        parts = re.split(r"[\s=]+", line, maxsplit=1)
        if len(parts) == 2:
            rem[parts[0].upper()] = parts[1].strip()
    return rem


def count_atoms(mol_lines):
    """Atoms in $molecule (Cartesian or Z-matrix), ghosts included."""
    if not mol_lines or mol_lines[0].lower().startswith("read"):
        return None
    n = 0
    for line in mol_lines[1:]:  # first line is charge and multiplicity
        tok = line.split()
        if tok and re.match(r"^@?[A-Za-z]{1,2}\d*$", tok[0]):
            n += 1
    return n


def check(path):
    text = open(path, errors="replace").read()
    sec = sections(text)
    rem = rem_dict(sec.get("rem", []))
    found = []

    def add(level, msg, ref):
        found.append((level, msg, ref))

    if "rem" not in sec:
        add("ERROR", "no $rem section found", "-")
        return found
    if "molecule" not in sec:
        add("ERROR", "no $molecule section found", "-")

    val = lambda k: rem.get(k, "").lower()
    cc = rem_dict(sec.get("complex_ccman", []))  # CAP / projected-CAP parameters live here
    ccval = lambda k: cc.get(k, "").lower()
    complex_on = val("COMPLEX_CCMAN") in ("true", "1")
    is_cap = complex_on or any(k in cc for k in ("CAP_ETA", "CAP_TYPE", "CAP_X", "PROJ_CAP"))
    eom_kinds = [k for k in ("EE_STATES", "IP_STATES", "EA_STATES", "DIP_STATES", "DIP_SINGLETS", "DIP_TRIPLETS",
                             "DEA_STATES", "SF_STATES", "EE_SINGLETS", "EE_TRIPLETS") if k in rem]
    has_dip = any(k.startswith("DIP") for k in eom_kinds)

    # Mixed / general basis must list every atom, ghosts included.
    if val("BASIS") in ("mixed", "gen"):
        nat = count_atoms(sec.get("molecule", []))
        blocks = sum(1 for l in sec.get("basis", []) if l.startswith("****"))
        if "basis" not in sec:
            add("ERROR", f"BASIS = {rem['BASIS']} but there is no $basis section", "eom-cc §1")
        elif nat is not None and val("BASIS") == "mixed" and blocks != nat:
            add("ERROR", f"BASIS = MIXED: $basis has {blocks} atom blocks but $molecule has {nat} atoms "
                         "(every atom, ghosts included, needs its own block)", "eom-cc §1")
        if val("BASIS") == "mixed" and any(re.match(r"^\[.*,.*\]$", rem.get(k, "")) for k in eom_kinds):
            add("WARN", "per-irrep state list with BASIS = MIXED: mixed basis turns symmetry off, "
                        "so only the first entry is meaningful", "eom-cc §1")

    # CAP / complex EOM needs tight Davidson convergence.
    if is_cap and eom_kinds:
        conv = rem.get("EOM_DAVIDSON_CONVERGENCE")
        if conv is None or (conv.isdigit() and int(conv) < 7):
            add("ERROR", f"CAP/complex EOM with EOM_DAVIDSON_CONVERGENCE = {conv or 'default (5)'}; "
                         "use 7 or tighter (loose convergence changed widths by +20 to +135 %)", "eom-cc §2")
        if has_dip:
            add("WARN", "CAP with EOM-DIP: not available in Q-Chem 6.3.1 (forum #3172); check your version",
                "eom-cc §5")

    # Complex (CAP / CS / CBF) code: the $complex_ccman block is mandatory.
    if complex_on and "complex_ccman" not in sec:
        add("ERROR", "COMPLEX_CCMAN is on but there is no $complex_ccman block: Q-Chem stops in the parser "
                     "within seconds (add the block with the CAP parameters, or PROJ_CAP 3 for a projected run)",
            "eom-cc §5a")
    if complex_on and any(k in rem for k in ("CC_FNO_THRESH", "CC_FNO_USEPOP")):
        add("ERROR", "FNO with COMPLEX_CCMAN failed in the group's runs (\"Key 'hf/c_o1b' is not known\"); "
                     "drop CC_FNO_THRESH / CC_FNO_USEPOP", "eom-cc §5a")

    # A box/sphere CAP is fixed in the input frame; Q-Chem's reorientation moves the molecule.
    if any(k in cc for k in ("CAP_X", "CAP_Y", "CAP_Z")) and ccval("CAP_TYPE") != "2":
        keeps_frame = (val("SYM_IGNORE") in ("true", "1") or val("SYMMETRY") in ("false", "0")
                       or val("POINT_GROUP_SYMMETRY") in ("false", "0"))
        if not keeps_frame:
            add("WARN", "CAP box set but nothing stops Q-Chem reorienting the molecule (the box stays at the "
                        "input origin); centre the molecule and set SYMMETRY false / SYM_IGNORE TRUE, unless "
                        "your input is already in Q-Chem's standard orientation", "eom-cc §5a")

    # Projected CAP (PROJ_CAP 3): densities for pyopencap are exported only with GUI = 2.
    # CC_TRANS_PROP is not needed: the manual (6.3, p. 583) exports them with GUI = 2 + PROJ_CAP 3,
    # and the group's working EOM-IP runs did not set it.
    if ccval("PROJ_CAP") == "3" and val("GUI") != "2":
        add("INFO", "PROJ_CAP 3 without GUI = 2: Q-Chem prints its own trajectories, but the state and "
                    "transition densities pyopencap needs are written to the .fchk only with GUI = 2",
            "pyopencap §1")

    # EOM_USER_GUESS traps.
    if val("EOM_USER_GUESS") in ("true", "1"):
        if has_dip:
            add("WARN", "EOM_USER_GUESS with DIP states crashed (double free) at the DIP stage in the group's "
                        "runs; use EOM_SHIFT (units of 1e-3 Eh) instead", "eom-cc §5")
        if ccval("PROJ_CAP") == "3":
            add("WARN", "EOM_USER_GUESS with projected CAP: only the guessed roots are printed, but pyopencap "
                        "needs all N states; aim the roots with EOM_SHIFT instead", "pyopencap §1")

    # Oscillator strengths need CC_TRANS_PROP.
    if any(k.startswith("EE") for k in eom_kinds) and val("CC_TRANS_PROP") not in ("true", "1"):
        add("INFO", "EE states without CC_TRANS_PROP = TRUE: no oscillator strengths will be printed", "eom-cc §4")

    # Frozen core: only true core.
    if "CC_FROZEN_CORE" in rem:
        add("ERROR", "CC_FROZEN_CORE is not a Q-Chem keyword (the job crashed); use N_FROZEN_CORE", "eom-cc §2")
    if "N_FROZEN_CORE" in rem and rem["N_FROZEN_CORE"].lower() not in ("fc", "0", "false"):
        add("INFO", f"N_FROZEN_CORE = {rem['N_FROZEN_CORE']}: freeze only true core; more can swap orbital "
                    "order between charge states", "eom-cc §2")

    return found


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    bad = False
    for path in argv[1:]:
        try:
            found = check(path)
        except OSError as e:
            print(f"{path}: cannot read ({e})")
            bad = True
            continue
        if not found:
            print(f"{path}: OK (no known problems found)")
        for level, msg, ref in found:
            print(f"{path}: {level}: {msg}  [{ref}]")
            bad |= level == "ERROR"
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
