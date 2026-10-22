#!/usr/bin/env python3
"""Check whether a Q-Chem job really finished and whether its EOM roots are usable.

Usage: python3 check_qchem_output.py job.out [job2.out ...]
Exit code 1 if any ERROR was found.

Rules come from the group's notes: a job counts as finished only if the output
ends with "Thank you very much" AND the matching .err file is clean (never trust
sacct COMPLETED). Failure-message matching is a heuristic: Q-Chem's wording
varies between versions, so read the flagged lines.
"""
import os
import re
import sys

ROOT = re.compile(r"^\s*(EOM[\w-]*)\s+transition\s+(\d+)/(\S+)")
EXC = re.compile(r"Excitation energy\s*=\s*(-?[\d.]+)\s*eV")
R1 = re.compile(r"R1\^2\s*=\s*([\d.]+)")
RES = re.compile(r"Res\^2\s*=\s*([\d.eE+-]+)")
FAIL = re.compile(r"(not converged|did not converge|failed to converge|fatal error|"
                  r"error occurred|aborting|segmentation fault|killed)", re.I)
STATES = re.compile(r"^\s*(EE_STATES|EE_SINGLETS|EE_TRIPLETS|IP_STATES|EA_STATES|DIP_STATES|"
                    r"DEA_STATES|SF_STATES|DSF_STATES|DIP_SINGLETS|DIP_TRIPLETS|IP_ALPHA|IP_BETA|EA_ALPHA|EA_BETA)\s*=?\s*\[?([\d,\s]+)\]?", re.I)


def check(path):
    found = []
    add = lambda lvl, msg: found.append((lvl, msg))
    text = open(path, errors="replace").read()
    lines = text.splitlines()

    if "Thank you very much" not in text:
        add("ERROR", "no 'Thank you very much' line: the job did not finish normally "
                     "(time limit, memory, scratch or a crash). Check the end of the file and the .err file")

    err = os.path.splitext(path)[0] + ".err"
    if os.path.exists(err):
        bad = [l.strip() for l in open(err, errors="replace") if FAIL.search(l) or "error" in l.lower()]
        if bad:
            add("ERROR", f"{os.path.basename(err)} has error lines, e.g.: {bad[0][:120]}")

    for i, l in enumerate(lines):
        if FAIL.search(l) and "Davidson procedure converged" not in l:
            add("WARN", f"line {i + 1}: {l.strip()[:120]}")

    # Requested vs found roots (requested counts are read from the echoed $rem).
    requested = 0
    for l in lines[:2000]:
        m = STATES.match(l)
        if m:
            requested += sum(int(x) for x in re.findall(r"\d+", m.group(2)))
    roots = []
    for i, l in enumerate(lines):
        m = ROOT.match(l)
        if not m:
            continue
        block = "\n".join(lines[i:i + 4])
        e, r1, res = EXC.search(block), R1.search(block), RES.search(block)
        roots.append((m.group(1), int(m.group(2)), m.group(3),
                      float(e.group(1)) if e else None,
                      float(r1.group(1)) if r1 else None,
                      float(res.group(1)) if res else None))
    if requested or roots:
        msg = f"{len(roots)} EOM roots printed"
        if requested:
            msg += f", {requested} requested"
        add("INFO", msg)
        if requested and len(roots) < requested:
            add("WARN", f"{requested - len(roots)} requested roots are missing: often near-degenerate roots "
                        "stalling Davidson. Ask for more roots, add guesses, or split by symmetry (eom-cc §2)")
    sats = [r for r in roots if r[4] is not None and r[4] < 0.5]
    if sats:
        add("INFO", f"{len(sats)} root(s) with R1^2 < 0.5 are satellites (2h1p/2p2h), not main lines: "
                    + ", ".join(f"{k} {n}/{s} {e:.3f} eV" for k, n, s, e, _, _ in sats[:6] if e is not None)
                    + (" ..." if len(sats) > 6 else "") + "  (eom-cc §3)")
    loose = [r for r in roots if r[5] is not None and r[5] > 1e-4]
    if loose:
        add("WARN", f"{len(loose)} root(s) with Res^2 > 1e-4 (largest {max(r[5] for r in loose):.1e}); "
                    "treat them as unconverged")
    if roots:
        es = [r[3] for r in roots if r[3] is not None]
        if es:
            add("INFO", f"root energies span {min(es):.3f} to {max(es):.3f} eV. Identify roots by character "
                        "(fragment weights, NTOs), never by energy order (eom-cc §3)")

    if re.search(r"^\s*(CAP_ETA|CAP_TYPE|COMPLEX_CCMAN)\b", text, re.M | re.I):
        add("INFO", "CAP job: report widths from a deperturbed eta trajectory with a channel-closed control, "
                    "not a single raw value (eom-cc §5)")
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
        if not any(l != "INFO" for l, _ in found):
            print(f"{path}: OK (finished normally; no known problems found)")
        for level, msg in found:
            print(f"{path}: {level}: {msg}")
            bad |= level == "ERROR"
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
