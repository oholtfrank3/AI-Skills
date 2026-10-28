# Worked example: Ar 3s holes at an Ar(111)–water interface (2026)

How the method choices in one real project were made, including the ones that failed. Use it as a pattern for reasoning, not as a template for settings.

## The question
Experiment (Grieves & Orlando 2011) saw signals near the Ar 3s⁻¹ energy for argon-capped water. Do Ar 3s holes decay by ICD or ETMD involving the water, and do holes move toward the water first?

Broken into observables:
1. Hole energies per site, and how the water shifts them (static).
2. Whether each decay channel is energetically open (hole vs two-site dication).
3. Decay widths Γ for the open channels.
4. Hole migration in time (does the hole reach the water before it decays?).

## What was chosen, and why

| Observable | Method chosen | Validation that justified it | What did not work |
|---|---|---|---|
| Site hole energies | EOM-IP-CCSD/aug-cc-pVDZ on hole-centred clusters, Dyson + Pipek–Mezey localized | couplings vs MRCI+Q on Ar₂ (18.1 vs 17.5 meV); cluster-size convergence of the water shift (−357 vs −355 meV) | SA-CASSCF/cc-pVDZ compressed site offsets ~2× (too little polarization) |
| Channel open/closed | experimental fragment IPs + computed environment shifts | monomer IPs at EOM-IP-CCSD, EOM-IP-CCSD*, ΔCCSD(T), aDZ→aQZ against experiment | raw EOM hole energy was +0.6 eV off; using it made the margins meaningless |
| Widths | CAP-EOM-IP-CCSD with deperturbed η trajectories and a null control | relative widths across geometries reproduced, not just distance trends | projected CAP (pyopencap): uncorrected widths 15–300× too large and corrected ≈ 0 at 5–10 states, and 10²–10⁴× too large and still not converged at 30 states; complex basis functions gave negative widths; picking η by the velocity minimum landed on grid edges and spikes for these sub-meV widths. (An early worry that the in-method 2h1p continuum sat ~1.5 eV too low was wrong: those roots were bound satellites, and the continuum began near the EOM-DIP threshold.) |
| Migration | DIM model Hamiltonian (one hole state per Ar, self-consistent polarization) validated against EOM-CC, dynamics with CSDM in SHARC | blind EOM water shifts, MAE 4.5 meV; FSSH-EDC vs CSDM contact weight 0.19 vs 0.20 | RT-TDDFT and Ehrenfest (TiDES, CASSCF) self-trapped the hole and collapsed the water onto Ar |

## The general lessons
- Split a big question into static observables first. They are cheaper and they validate the dynamics later.
- A direct ab initio approach that fails (here, mean-field dynamics) can still point to the right model, as long as the model is validated against a higher-level method on points it was not fitted to.
- Errors at the two ends of a channel (the hole and the final state) need separate correction.
- No single CAP diagnostic (plateau, ξ, deperturbation) separated real widths from artefacts; a matched channel-closed null did.
- Most of the cost went into failed set-ups that a small benchmark would have caught. Benchmark first.
