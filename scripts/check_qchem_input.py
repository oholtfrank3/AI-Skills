#!/usr/bin/env python3
"""Check a Q-Chem input for mistakes that have cost the group jobs.

Usage: python3 check_qchem_input.py job.in [job2.in ...]
Exit code 1 if any ERROR was found, else 0. Each finding cites the skill
section it comes from. Not a full parser: it reads $molecule, $rem and $basis.
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
    is_cap = any(k in rem for k in ("CAP_ETA", "CAP_TYPE", "CAP_X", "PROJ_CAP")) or val("COMPLEX_CCMAN") in ("true", "1")
    eom_kinds = [k for k in ("EE_STATES", "IP_STATES", "EA_STATES", "DIP_STATES", "DEA_STATES", "SF_STATES",
                             "EE_SINGLETS", "EE_TRIPLETS") if k in rem]

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
        if "DIP_STATES" in rem:
            add("WARN", "CAP with EOM-DIP: not available in Q-Chem 6.3.1 (forum #3172); check your version",
                "eom-cc §5")
    if val("PROJ_CAP") and val("GUI") != "2":
        add("WARN", "projected CAP needs GUI = 2 so the .fchk with densities is written", "pyopencap §1")
    if val("PROJ_CAP") and val("CC_TRANS_PROP") not in ("true", "1"):
        add("WARN", "projected CAP needs CC_TRANS_PROP = TRUE for state-to-state densities", "pyopencap §1")

    # Oscillator strengths need CC_TRANS_PROP.
    if any(k.startswith("EE") for k in eom_kinds) and val("CC_TRANS_PROP") not in ("true", "1"):
        add("INFO", "EE states without CC_TRANS_PROP = TRUE: no oscillator strengths will be printed", "eom-cc §4")

    # Frozen core: only true core.
    if "N_FROZEN_CORE" in rem and rem["N_FROZEN_CORE"].lower() not in ("fc", "0"):
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
