# Excess proton in water: CP2K AIMD

190 atoms (64 H₂O + H⁺, charge +1) in a 12.42 Å periodic cube, PBE-D3 with GTH pseudopotentials and DZVP-GTH basis, 400 Ry cutoff, OT SCF, NVT at 300 K with a GLE thermostat, 0.5 fs step, 2000 steps requested. `WALLTIME 1800` stops the run cleanly after 30 min; restart from `WATER-1.restart` to continue.

**Question it answers:** what the excess proton looks like in water (Eigen H₉O₄⁺ vs Zundel H₅O₂⁺) and how it hops between waters (Grotthuss shuttling). Follow the O atom that has three H within ~1.2 Å along `WATER-pos-1.xyz`.

**Expected** (CP2K 2022.1, 24 ranks on PACE, about 4 s per step after the first):

| | Value |
|---|---|
| Potential energy, step 0 | −1086.04996 Eh |
| Conserved quantity, step 0 → 385 (192.5 fs) | −1085.77920 → −1085.77868 Eh |
| Temperature | fluctuates 290–310 K |
| SCF | converges in 1–2 outer cycles per step |

**Checks before trusting it:** the conserved quantity (`Cons Qty` in `WATER-1.ener`) should drift by well under 1 mEh per 100 fs here; a steady climb means the SCF tolerance or time step is too loose (`cp2k` skill §5). Count the H atoms within 1.2 Å of each O: exactly one O should have three.

**Notes**
- The original tutorial also had a non-equilibrium start (proton placed away from equilibrium) with the same input; only `water.xyz` differs.
- `DZVP-GTH` from `HFX_BASIS` is kept for reproducibility. For new work use `DZVP-MOLOPT-SR-GTH` from `BASIS_MOLOPT` (`cp2k` skill §2).
- The GLE matrix (`A_LIST`) is a ready-made thermostat from the GLE4MD library; don't edit it by hand.
- Not re-run with a current CP2K; numbers are from the original tutorial outputs.
