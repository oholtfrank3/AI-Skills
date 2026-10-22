#!/usr/bin/env python3
"""Check energy conservation and hops in SHARC output.lis files (sharc skill §4).

Usage: python3 check_sharc_lis.py [--tol-pct 1] [--jump-mev 5] [--absorbing] output.lis [...]

Columns (SHARC 3.0 manual §5): step, time (fs), diag state, MCH state, Ekin, Epot,
Etot (eV), gradient RMS, dipole, spin, wall time. Lines starting with '#' are
headers or hop events ("# Surface Hop: new state= ... old state= ...").

Drift is judged against the mean kinetic energy, never against the absolute
total energy (arbitrary zero). Use --absorbing for runs with an absorbing edge,
where Etot is not conserved by construction.
Exit code 1 if any ERROR was found.
"""
import argparse
import statistics
import sys


def read(path):
    rows, hops, frustrated = [], 0, 0
    for line in open(path, errors="replace"):
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            low = s.lower()
            if "surface hop" in low:
                hops += 1
            if "frustrated" in low:
                frustrated += 1
            continue
        p = s.split()
        if len(p) >= 7:
            try:
                rows.append((int(p[0]), float(p[1]), int(p[2]), float(p[4]), float(p[5]), float(p[6])))
            except ValueError:
                pass
    return rows, hops, frustrated


def check(path, tol_pct, jump_mev, absorbing):
    found = []
    add = lambda lvl, msg: found.append((lvl, msg))
    rows, hops, frus = read(path)
    if len(rows) < 2:
        add("ERROR", "fewer than 2 time steps found: the run died early or this is not an output.lis")
        return found
    t0, t1 = rows[0][1], rows[-1][1]
    etot = [r[5] for r in rows]
    ekin = statistics.fmean(r[3] for r in rows)
    drift = (etot[-1] - etot[0]) * 1000
    steps = [(abs(etot[i] - etot[i - 1]) * 1000, rows[i][1]) for i in range(1, len(rows))]
    jump, tjump = max(steps)
    add("INFO", f"{len(rows)} steps, {t0:.2f}-{t1:.2f} fs; {hops} hops"
                + (f", {frus} frustrated" if frus else "") + f"; mean Ekin {ekin:.3f} eV")
    add("INFO", f"Etot drift {drift:+.2f} meV (end - start); largest single-step change {jump:.2f} meV at {tjump:.2f} fs")
    if absorbing:
        add("INFO", "absorbing edge: Etot is not conserved by construction; drift not judged")
        return found
    if ekin > 0:
        pct = abs(drift) / (ekin * 1000) * 100
        lvl = "ERROR" if pct > 5 * tol_pct else "WARN" if pct > tol_pct else "INFO"
        add(lvl, f"drift is {pct:.2f} % of the mean kinetic energy (tolerance {tol_pct} %)")
    if jump > jump_mev:
        add("WARN", f"single-step jump of {jump:.1f} meV > {jump_mev} meV: look for a hop, a trivial crossing or a "
                    "restart at that time (sharc §3-4)")
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+")
    ap.add_argument("--tol-pct", type=float, default=1.0, help="drift tolerance, %% of mean Ekin (default 1)")
    ap.add_argument("--jump-mev", type=float, default=5.0, help="flag single-step Etot changes above this (meV)")
    ap.add_argument("--absorbing", action="store_true", help="run has an absorbing edge (Etot not conserved)")
    a = ap.parse_args()
    bad = False
    for path in a.files:
        try:
            found = check(path, a.tol_pct, a.jump_mev, a.absorbing)
        except OSError as e:
            print(f"{path}: cannot read ({e})")
            bad = True
            continue
        if not any(l != "INFO" for l, _ in found):
            print(f"{path}: OK (energy conserved within tolerance)")
        for level, msg in found:
            print(f"{path}: {level}: {msg}")
            bad |= level == "ERROR"
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
