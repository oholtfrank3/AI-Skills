# EOM-CCSD and CAP-EOM-CCSD (Q-Chem 6.x, PySCF): troubleshooting reference

Last researched: 2026-10-21

**How to use this file:** find your symptom under "Known issues and fixes", check the cause against your output, apply the fix, and check the setup on a starter calculation before you trust a production run. The group's own rules are in `skills/eom-cc/SKILL.md`. This file adds the sources behind them and does not repeat them. When you answer, give the user the one fix that best fits (with its keywords or code) and offer the rest; multi-step fix orders below are for you (`troubleshooting` §2).

---

## Official documentation

Q-Chem links point to the **6.4** manual, which matches what we run. `manual.q-chem.com/latest/` now serves **7.0**, where the same pages are numbered 7.9.x, not 7.10.x. The page file names are the same, so swapping `6.4` for `latest` works.

**EOM-CC job control (7.10.18):** <https://manual.q-chem.com/6.4/sub_ccjobcontol.html>
- **Choosing the method:** set `METHOD = EOM-CCSD` and request a number of roots with `XX_STATES`. Tables 7.1/7.2 list which state types work in CCMAN2 and which only in the old CCMAN.
- **`EE_STATES` / `EE_SINGLETS` / `EE_TRIPLETS`:** roots per irrep, e.g. `[2,2,0,0]`. SINGLETS/TRIPLETS work only with a closed-shell reference.
- **`IP_STATES`, `EA_STATES`, `DIP_STATES`, `SF_STATES`, `DEA_STATES`:** the same array format. IP removes a beta electron by default (`IP_ALPHA`/`IP_BETA` choose). `DSF_STATES` (2SF) is CCMAN only.
- **Symmetry of the array:** the array gives the symmetry of the *transition*, not of the target state. For an open-shell reference, target irrep = reference irrep × transition irrep.
- **Root count can change:** Q-Chem may raise the root count if it suspects degeneracy, or lower it if it cannot build enough guesses.
- **Davidson settings:** `EOM_DAVIDSON_CONVERGENCE` (default 5, i.e. 1e-5 on the residual), `EOM_DAVIDSON_THRESHOLD` (keep it equal to, or a little looser than, the convergence value), `EOM_DAVIDSON_MAXVECTORS` (default 60 per root; more = smoother convergence but more disk) and `EOM_DAVIDSON_MAX_ITER` (default 30).
- **Guess settings:** `EOM_NGUESS_SINGLES` (default = number of roots), `EOM_NGUESS_DOUBLES`, `EOM_PRECONV_SINGLES` (default 0; 1 = solve in the singles space first) and `EOM_PRECONV_DOUBLES` (for DIP/DEA/DSF; not available for EE in CCMAN2).
- **Targeting specific states:** `EOM_USER_GUESS` (CCMAN2 only) and `EOM_SHIFT` (n × 1e-3 Eh; finds the roots nearest that energy).
- **Inner-valence states:** `EOM_EE_IV_PROJ` / `EOM_IP_IV_PROJ` project the solver onto inner-valence orbitals (6.4+).
- **FNO and charge stabilization:** `CC_FNO_THRESH`/`CC_FNO_USEPOP` for frozen natural orbitals; `ADD_CHARGED_CAGE`, `CAGE_*` and `SCALE_NUCLEAR_CHARGE` for charge stabilization.

**Guess formation and Davidson (7.10.16):** <https://manual.q-chem.com/6.4/subsec_EOM-CC-diag.html>
- **Default guess:** Koopmans-like singles, one per requested root. CCMAN2 adds doubles guesses if it runs out of singles.
- **`$eom_user_guess` format:** EE takes `occ virt` pairs. IP/EA take a single list of orbital numbers, counted in the order printed at the top of the CCMAN2 output.
- **Ask for enough roots:** `XX_STATES` must request enough roots in each irrep for the user guess to be used.

**Inner-valence projectors (7.10.17):** <https://manual.q-chem.com/6.4/subsec_EOM-CC-ivproj.html>

**Metastable states: CAP, complex scaling, CBF (7.10.9):** <https://manual.q-chem.com/6.4/sub_cc_cs_cap.html>
- **`COMPLEX_CCMAN = TRUE`** turns on the complex code (CCMAN2 only). The parameters go in a `$complex_ccman` block.
- **CAP units:** `CAP_ETA` is in units of 1e-5 Eh (`200` = 0.002). `CAP_X/Y/Z` are box onsets in units of 1e-3 bohr. `CAP_TYPE` is 0 = sphere, 1 = cuboid, 2 = smooth Voronoi (the onset then goes in `CAP_X`). `CAP_RE_ETA` adds a real absorbing potential.
- **Complex scaling:** `CS_THETA` (in 1e-3 rad) and `CS_ALPHA`. For CAP-EOM, only `CS_HF = CS_CCSD = TRUE` is implemented.
- **Integration grid:** the CAP is integrated numerically on a (99,590) grid by default. The output compares the numerical and analytic overlap matrices; if they disagree, change `XC_GRID`.
- **Properties:** `CC_EOM_PROP = 1` is switched on automatically for CAP, because the first-order deperturbation correction needs it.
- **Projected CAP (`PROJ_CAP`):** 1 = projected CAP in CCSD and EOM; 2 = EOM step only, with real T amplitudes, so `ETA_STEP`/`NSTEPS` give a cheap η-trajectory; 3 = CAP projected onto pre-computed EOM states, with `PROJ_PROP = 1` for first-order corrections. Options 1 and 2 are EE/EA only.
- **Gradients:** analytic gradients exist only for a cuboid CAP with `CS_HF = TRUE`, and frozen core is turned off for them.
- **Complex RI:** works for CCSD and EOM-IP/EA/EE/SF. Set `AUX_BASIS`; CBF jobs also need `COMPLEX_AUX_BASIS`.

**Worked examples (7.10.19):** <https://manual.q-chem.com/6.4/ex_CAPlibwfa.html>. The useful ones are 7.90 (water EE with Cholesky decomposition), 7.93 (NO3 IP from an anion reference), 7.98 (EA with a user guess), 7.101 (DIP with a charged cage), 7.107 (CAP-EOM-EA for N2⁻), 7.109 (Voronoi CAP for CO⁻) and 7.110–7.112 (projected CAP trajectories). The same inputs ship in `$QC/samples/ccman2`.

**Memory and back-ends (6.17.4):** <https://manual.q-chem.com/6.4/Ch6.S17.SS4.html>
- **`CC_MEMORY`:** defaults to 50 % of `MEM_TOTAL`, or 1.5 GB if `MEM_TOTAL` is unset. The manual suggests 75–80 % of node RAM when CCMAN2 has the node to itself.
- **`MEM_STATIC`:** capped at 8191 MB since 6.0.
- **`CC_BACKEND`:** `VM` (default, disk-based), `XM` (for large jobs on limited memory) or `INCORE` (small jobs).

**Other relevant pages:** frozen natural orbitals <https://manual.q-chem.com/6.4/sec_FNO.html>, Dyson orbitals <https://manual.q-chem.com/6.4/topic_dyson.html>, CVS core states <https://manual.q-chem.com/6.4/sub_cvs_eom.html>.

**PySCF CC user guide:** <https://pyscf.org/user/cc.html>
- **Function calls:** `mycc.ipccsd(nroots=)`, `eaccsd`, `eeccsd` (all spin multiplicities), `eomee_ccsd_singlet`/`_triplet` (RHF only), `eomsf_ccsd`.
- **Return values:** EOM energies are differences from the CCSD ground state, in Hartree (confirmed in issue #2235).
- **`koopmans=True`:** keeps the roots with large R1 (single-excitation) weight. Without it, PySCF returns the lowest roots, which may include doubles-dominated ones.
- **Custom guess:** pass `guess=` a vector built with `amplitudes_to_vector_ee`/`_ip`/`_ea`.
- **Restart:** needs `mf.chkfile` plus the CCSD DIIS file (see `examples/cc/32-restart.py`).

**PySCF examples:** <https://github.com/pyscf/pyscf/tree/master/examples/cc>
- **`20-ip_ea_eom_ccsd.py`:** RCCSD, UCCSD and GCCSD IP/EA/EE on O2.
- **`23-eom_ee_oscillator_strength.py`:** transition dipoles and oscillator strengths. This needs PR #3480, which was merged on master 2026-10-11 and is **not in v2.14.0**.
- **Others:** `11-frozen_core.py`, `22-fnoccsd.py`, `32-restart.py`.

**PySCF EOM object defaults** (read from `pyscf/cc/eom_rccsd.py` on master, 2026-10-21):
- **Davidson settings:** `max_space = 20`. `conv_tol` and `max_cycle` are copied from the CCSD object.
- **Complex roots are dropped:** without a user guess or `koopmans`, any root with |Im E| > 1e-3 is thrown away (the `pickeig` function).
- **No error on failure:** `kernel` returns a per-root `conv` flag and does not raise if a root fails to converge. Always check `conv`.

---

## Starter calculations

Run one of these before a production job to check your input style and your machine.

**1. EOM-IP-CCSD of water (Q-Chem or PySCF)**
- **System:** H2O, closed-shell RHF reference, aug-cc-pVTZ, frozen core.
- **Q-Chem input:** `METHOD EOM-CCSD`, `BASIS aug-cc-pVTZ`, `N_FROZEN_CORE FC`, `IP_STATES [1,0,1,1]`. Q-Chem orders the C2v irreps A1, A2, B1, B2, and the orientation decides which of B1/B2 holds the 1b1 and 1b2 holes. Run once and check the irrep labels in the output.
- **PySCF input:** `cc.CCSD(mf, frozen=1).run().ipccsd(nroots=4)`. Multiply by 27.2114 for eV.
- **Expected:** EOM-IP-CCSD/aug-cc-pVTZ gives 12.594 (1b1⁻¹), 14.825 (3a1⁻¹) and 18.972 (1b2⁻¹) eV. FCI/aug-cc-pVTZ gives 12.679 / 14.915 / 19.024 eV; experiment is 12.6 / 14.8 / 18.7 eV. Source: Marie & Loos, arXiv:2402.13877, Table I (CC3/aug-cc-pVTZ geometry, frozen core). Expect differences of ~0.01 eV from geometry.
- **Resources:** seconds to minutes on one node.
- **Most common mistake:** using a symmetry-disabling basis (`BASIS = MIXED`) or `CC_SYMMETRY FALSE` while keeping a 4-irrep array. That fails with "Inconsistent with the number of irreps" (forum #171). In C1, use `IP_STATES [4]`.

**2. EOM-EE-CCSD singlets of water (Q-Chem)**
- **Input:** manual Example 7.90 (aug-cc-pVDZ, frozen core, `EE_SINGLETS [2,2,0,0]`). Add `CC_TRANS_PROP = TRUE` to get oscillator strengths.
- **Expected:** 1B1 (n→3s) is about 7.5 eV in aug-cc-pVDZ. The theoretical best estimate is 7.62 eV (exFCI/aug-cc-pVQZ), and exFCI/aug-cc-pVDZ is 7.53 eV (Loos et al. 2018, arXiv:1807.02045, Table 1). EOM-CCSD itself should be within about 0.1 eV (unverified for this exact basis).
- **Most common mistake:** expecting oscillator strengths without `CC_TRANS_PROP` (forum #1031). Also, in aug-cc-pVDZ these Rydberg states are not basis-converged.

**3. CAP-EOM-EA-CCSD of the N2⁻ ²Πg shape resonance (Q-Chem)**
- **Input:** manual Example 7.107. N2 at R = 1.0975 Å, with a ghost atom at the centre of mass carrying 3s3p3d diffuse shells. Basis is aug-cc-pVTZ plus those ghost shells.
- **Key settings:** `COMPLEX_CCMAN 1`, `EA_STATES [0,0,2,0,0,0,0,0]`, `FORCE_SYMMETRY_ON true`. In `$complex_ccman`: `CS_HF 1`, `CAP_TYPE 1`, `CAP_X/Y 2760`, `CAP_Z 4880`, `CAP_ETA 200`.
- **Scanning η:** run a scan over `CAP_ETA`, not one value. Or use `PROJ_CAP 2` with `ETA_STEP`/`NSTEPS` to get a cheap trajectory.
- **Expected:** E_R = 2.487 eV, Γ = 0.417 eV at η_opt = 0.0015 (Zuev et al., JCP 141, 024102 (2014)). A projected-CAP study found a second minimum at η = 0.007, with E_R = 2.617 and Γ = 0.395 eV (Gayvert & Bravaya, JCP 156, 094108 (2022)). Experiment is 2.316 / 0.414 eV (Berman et al. 1983). All values as tabulated in Burth, Kossoski & Loos, arXiv:2507.03496, Table II.
- **Most common mistake:** reading one raw complex energy at an arbitrary η. You must pick η from the trajectory, using the minimum of η|dE/dη|, and apply the deperturbation. Two minima can exist, so say which one you report.

**4. PySCF IP-EOM-CCSD with a check on satellites**
- **Input:** `mycc = cc.CCSD(mf, frozen=1).run(); e, v = mycc.ipccsd(nroots=8)`. Read `qpwt` (the R1 weight) from the log at `verbose >= 4`.
- **Expected:** the main lines match Starter 1. Satellites have small `qpwt`.
- **Quartet satellites:** PySCF RHF-based IP-EOM cannot produce quartet 2h1p satellites, while Q-Chem's spin-orbital code can (issue #2994). Do not count them as missing roots.
- **Most common mistake:** assuming `conv` is all True. Check it, and do not set it by hand (see the group notes).

---

## Known issues and fixes

### Davidson convergence and missing roots

- **Davidson misses a state (Q-Chem).** *Cause:* an iterative solver with a Koopmans guess. *Fix:* the developer-recommended order is (1) more guess vectors (`EOM_NGUESS_SINGLES`) with the same number of roots, (2) `EOM_PRECONV_SINGLES 1`, (3) tighter `EOM_DAVIDSON_CONVERGENCE`, (4) more roots (most expensive). Tell the user step 1 (with 2 if they want one rerun), not all four. [talk.q-chem #59, A. Krylov, 2020-07-03](https://talk.q-chem.com/t/how-to-troubleshoot-eom-calculations/59)
- **Roots with absurd energies, sudden low roots, "complex roots" warnings.** *Cause:* loss of spin or permutational symmetry from numerical noise. Treat the whole run as suspect. *Fix:* raise `EOM_DAVIDSON_MAXVECTORS`, ask for fewer roots or loosen the threshold, start from more guesses or preconverged singles. For CVS jobs, use `CVS_EOM_SHIFT`. (Same thread, #59.)
- **Benzene S1 missing in C1 (lowest root 6.38 instead of 4.86 eV).** *Cause:* without symmetry, the guess set did not include the S1 character. *Fix:* more guesses or preconverged singles; in the end the user needed 20 roots. Keep symmetry on when you can. [talk.q-chem #809, 2022-10-14](https://talk.q-chem.com/t/no-s1-state-for-benzene-when-eom-ccsd-is-used-without-symmetry/809)
- **Projected-CAP roots hit the maximum Davidson iterations at moderate-to-large η (pyrrole, Box and Voronoi CAP).** *Fix:* `EOM_PRECONV_SINGLES` plus a large `EOM_NGUESS_SINGLES`. [talk.q-chem #72, 2020-07-07](https://talk.q-chem.com/t/resonances-with-projected-cap/72)
- **PySCF EOM-EE returns roots 1, 2, 5 instead of 1, 2, 3 (He2).** *Cause:* the guess has the wrong spatial symmetry. *Fix:* ask for more roots, or perturb the guess. The issue is still open. [pyscf #254, 2018-11-27](https://github.com/pyscf/pyscf/issues/254)
- **PySCF IP-EOM misses satellites that Q-Chem finds (formamide).** *Cause:* these are not convergence failures. They are quartet 2h1p states, which the spin-adapted RHF IP code cannot represent. *Fix:* ignore them if you only want doublets. If you need them, a UHF- or GHF-based EOM may give them (unverified; not stated in the thread). [pyscf #2994, 2025-10-10 to 10-21](https://github.com/pyscf/pyscf/issues/2994)
- **PySCF root with tiny `qpwt` that other codes "miss" (H2/cc-pVDZ).** *Cause:* it is a real double excitation; FCI confirms it. PySCF also skipped some higher roots (possibly triplets). *Fix:* check R1 weight; use `koopmans=True` if you only want single-excitation states. [pyscf #3200, 2026-05](https://github.com/pyscf/pyscf/issues/3200)
- **`koopmans=True` makes higher roots odd.** *Cause:* it selects roots by overlap with the 1h/1p guess, not by energy. *Fix:* run either way and keep only roots with large `qpwt`. [pyscf #377, 2019-07-09](https://github.com/pyscf/pyscf/issues/377)
- **Inner-valence or 2s IPs out of Davidson reach.** *Fix:* CVS-type schemes (answer on MMSE). In Q-Chem, `EOM_IP_IV_PROJ`, `EOM_USER_GUESS` or `EOM_SHIFT` also do this. [MMSE #14541, 2025-10-06](https://mattermodeling.stackexchange.com/questions/14541)
- **PySCF Davidson preconditioner shift.** Every root uses the lowest root's shift. A per-root shift converges faster, but it changed which roots were selected in dense spectra, so it was not merged. This is a design choice, not a bug. [pyscf #3398, 2026-08-16](https://github.com/pyscf/pyscf/issues/3398)

### Symmetry and state labels

- **"EE_SINGLETS: Inconsistent with the number of irreps".** *Cause:* `BASIS = MIXED` (or finite-difference jobs) turns point-group symmetry off. *Fix:* use `BASIS = GEN` (per element; keeps symmetry), or give a C1 array. [talk.q-chem #171, 2020-11-30](https://talk.q-chem.com/t/symmetry-of-eom-ee-ea-ccsd/171)
- **C3v molecule run as Cs.** *Cause:* CC/EOM always works in the largest Abelian subgroup. Map the irreps back yourself. [talk.q-chem #251, 2021-03-04](https://talk.q-chem.com/t/eom-ccsd-problem-with-symmetry/251)
- **What does the EA_STATES irrep mean?** It is the irrep of the orbital the electron attaches to (the transition). The target irrep is that times the reference irrep. [talk.q-chem #3056, 2026-02-21](https://talk.q-chem.com/t/symmetry-of-eom-ea-ccsd-significance/3056)
- **Same EOM state reached from different SCF references, giving fake "different states" and fake crossings (RhCH2⁺, CoCH2⁺).** *Fix:* choose the reference from which the targets are single EOM operations. A higher-energy, spin-pure reference is fine. Check ⟨S²⟩. [talk.q-chem #924, 2023-02](https://talk.q-chem.com/t/choosing-eom-reference-scf-states/924)
- **Assigning state character from canonical MOs.** This misleads. Use NTOs, which do not depend on the orbital choice. Non-HF orbitals are allowed (SCF_GUESS READ with zero SCF cycles), but they are canonicalized by default. [talk.q-chem #79, 2020-07-10](https://talk.q-chem.com/t/is-it-valid-to-use-mos-other-than-canonical-hf-orbitals-to-run-eom-cc-calculations/79)
- **PySCF qpwt differs between RCCSD and UCCSD.** *Cause:* how R is normalized. Only L and R together are meaningful. [pyscf #541, 2020-03-06](https://github.com/pyscf/pyscf/issues/541)

### Memory, scratch and hangs

- **EOM job dies or "hangs" silently (naphthalene, cc-pVTZ, IP).** *Cause:* the Slurm OOM killer. The Q-Chem output shows no error; the Slurm log does. *Fix:* set `CC_MEMORY` explicitly, use `CC_BACKEND = XM` on small-memory nodes, use symmetry. [talk.q-chem #2956, 2025-11 to 2026-01](https://talk.q-chem.com/t/trouble-using-eom-ccsd-with-frozen-core/2956)
- **Crash at integral import (79 atoms).** *Cause:* not enough memory or disk for the transformation. *Fix:* keep `CC_MEMORY` ≤ 80 % of node RAM, clear stale scratch, use `CC_BACKEND = XM`. CCMAN2 is OpenMP only, so do not spread it over nodes with MPI. EOM(2,3) uses the old CCMAN code, so avoid it. [talk.q-chem #1161, 2023-07-17](https://talk.q-chem.com/t/error-in-eom-ee-ccsd-and-eom-ee-cc-2-3-calculation/1161)
- **Over-allocating memory made a small SF job crash.** *Fix:* go back to the defaults plus `CC_BACKEND = INCORE` for small jobs. [talk.q-chem #489, 2021-11-08](https://talk.q-chem.com/t/cant-calculate-more-states-using-eom-sf-ccsd-calculation-in-q-chem-5-4-0/489)
- **EOM-EA FREQ stalls before gradients.** *Cause:* 7 GB of RAM on 128 cores. *Fix:* `CC_BACKEND = XM` and fewer threads; the job then ran about 8× faster. [talk.q-chem #263, 2021-03-18](https://talk.q-chem.com/t/eom-ea-frequency-analysis-stalling/263)
- **Day-long "Computing CCSD intermediates" step and poor OpenMP scaling.** *Cause:* `CC_MEMORY` too small. *Fix:* give it about 75 % of RAM. Single-precision keywords (`CC_SINGLE_PREC`, `EOM_SINGLE_PREC`, ...) or RI/CD also help. [talk.q-chem #431, 2021-10-17](https://talk.q-chem.com/t/general-questions-regarding-eom-ccsd-calculations/431)
- **EA job ends with no error (guanine).** The developers could not reproduce it (it finished in 4 h on 32 cores). They suspect a cluster time or memory limit; check `ulimit -a` and the scheduler log. [talk.q-chem #829, 2022-11-02](https://talk.q-chem.com/t/eom-ea-ccsd-calculations-being-cut-off/829)
- **Large EOM job crashes with "Error: in the serial run" despite 8.6 TiB of scratch.** *Cause:* a failing disk. *Fix:* check the kernel logs or SMART; try `CC_BACKEND = XM`. [talk.q-chem #1461, 2024-04-15](https://talk.q-chem.com/t/is-this-too-little-resources/1461)
- **Warning "MEM_STATIC capped at 8191".** This is expected since 6.0; the big allocations follow `MEM_TOTAL`. [talk.q-chem #811, 2022-10-15](https://talk.q-chem.com/t/mem-static-capped-in-6-0-1/811)
- **PySCF EOM ignored `mycc.max_memory` (Davidson always used 2000 MB).** Fixed in PR #3001 (merged 2025-10-15), so check that your version is newer. [pyscf #3000, 2025-10-14](https://github.com/pyscf/pyscf/issues/3000)
- **PySCF IP wrong in aug-cc-pVQZ (methanol 9.77 instead of 11.08 eV).** *Cause:* an ao2mo bug at low memory. More memory was the workaround; fixed in 2020 (860c139). If large-basis results jump, raise `max_memory` and compare. [pyscf #629, 2020-06-09](https://github.com/pyscf/pyscf/issues/629)
- **PySCF EOM with `mycc.direct = True` crashes in Wvvvv.** AO-direct is supported for ground-state CCSD only. [pyscf #2491, 2024-10-29](https://github.com/pyscf/pyscf/issues/2491)

### CAP and complex-valued EOM

- **CS-EOM-EA input ignores the EOM part.** *Cause:* `$complex_ccman` needs integers (`1`), not `true`. The developers also recommend CAP or CBF over plain complex scaling. [talk.q-chem #3039, 2026-02-06](https://talk.q-chem.com/t/complex-scaling-on-q-chem/3039)
- **Where is the resonance width?** For CAP/ADC, the developers analyse trajectories afterwards (e.g. pyopencap). For CAP-EOM, a developer says to look at the imaginary part of the energy. The standard definition is Γ = −2 Im(E), taken from the corrected trajectory. [talk.q-chem #709, 2022-07-26](https://talk.q-chem.com/t/how-to-find-resonance-width-in-an-output-file/709)
- **How to size the CAP box.** Use ⟨X²⟩, ⟨Y²⟩, ⟨Z²⟩ printed with `CC_REF_PROP = TRUE` (CCSD) or `CC_EOM_PROP = TRUE` (EOM), following Zuev 2014. See the Jagau/Bravaya/Krylov review (Annu. Rev. Phys. Chem. 68, 525). [talk.q-chem #3144, 2026-07-06](https://talk.q-chem.com/t/some-doubt-regarding-cap-onset/3144)
- **CAP + DIP is not available ("CS-EOMDIP-CCSD model is not available", 6.3.1).** CAP + IP + `CC_DO_DYSON` works on its own, and IP→DIP Dyson orbitals work without a CAP. Owen asked whether 6.4/7.0 adds this; no reply as of 2026-10-21. [talk.q-chem #3172, 2026-09-02](https://talk.q-chem.com/t/dyson-orbitals-between-eom-ip-and-eom-dip-states-with-a-cap-active/3172)
- **CAP-EOM-EA for N2⁻ has two η-trajectory minima** (η 0.0015 vs 0.007). This appears to be a general CAP problem that is still unresolved; report which minimum you used (Burth et al., arXiv:2507.03496).

### Method availability and accuracy

- **EOM-IP/EA-CCSD(fT) crash "Index does not correspond to a canonical block".** Fixed in 6.1.1. (dT) is EE only. [talk.q-chem #171, 2023-11-17](https://talk.q-chem.com/t/symmetry-of-eom-ee-ea-ccsd/171)
- **EOM-CC(2,3) crashes in 6.1.1.** It is old CCMAN code. Use EOM-EE-CCSDT (6.2.2+). [talk.q-chem #1724, 2024-11-29](https://talk.q-chem.com/t/ccman-error-with-eom-cc-2-3-in-q-chem-v-6-1-1/1724)
- **EOM-2SF (DSF) does nothing with `METHOD = EOM-CCSD`.** It is CCMAN only: set `CCMAN2 = false` with `EOM_CORR SDT` and doubles guesses. No CBF variant exists. [talk.q-chem #1619, 2024-08-28](https://talk.q-chem.com/t/non-performing-of-dsf-calcuation-at-eom-ccsd-level/1619)
- **FNO with EOM-EE loses states.** FNO drops diffuse virtuals, so Rydberg, EA and EE states can disappear. It is safe for IP, DIP and SF. Symmetry is turned off with FNO. [talk.q-chem #76, 2020-07-07](https://talk.q-chem.com/t/is-fno-approximation-applicable-to-eom-ee-ccsd/76)
- **Open-shell cation targets:** use the closed-shell neutral as the reference with `IP_STATES`, not a cation reference with EE. [talk.q-chem #571, 2022-02-06](https://talk.q-chem.com/t/i-wander-and-lost-around-eom-calculation/571)
- **EA PES of O2 fails beyond 3 Å, and UHF-CCSD(T) dissociation is badly wrong.** *Cause:* multireference character. *Fix:* scan point by point with `SCF_GUESS READ`, starting at long range. Another option is IP-EOM from the closed-shell O2²⁻. [talk.q-chem #2894, 2025-09 to 10](https://talk.q-chem.com/t/problem-oxygen-potential-energy-scan-using-ccsd-t-and-ea-state-pes-using-ea-eom-ccsd/2894)
- **Participator vs spectator Auger channels:** these correspond to R1² ≈ 1 (1h) and R2² ≈ 1 (2h1p) EOM-IP states. 2h1p energies are overestimated. [talk.q-chem #1031, 2023-05-03](https://talk.q-chem.com/t/how-to-get-oscillator-strength-eom-ccsd/1031)
- **PySCF H2/STO-3G `eeccsd` gives 2 roots; H atom UCCSD crashes.** Roots are capped at the vector size, and a 1-electron system has no doubles. Use a real basis, or CIS/CASCI for 1-electron systems. [pyscf #1400](https://github.com/pyscf/pyscf/issues/1400), [#1822](https://github.com/pyscf/pyscf/issues/1822)

### PySCF star corrections and degenerate roots

- **`ipccsd_star`/`eaccsd_star` errors of 1e-6 to 1e-2 Eh, varying from run to run.** *Cause:* left and right vectors were paired by index inside a degenerate block.
- **Fixes:** PR #3316 (merged 2026-07-15) pairs roots by overlap. PR #3404 (merged 2026-08-19) biorthonormalizes left vectors within a degenerate cluster for GCCSD.
- **Warning still printed:** a right root with no matching converged left root still logs "Will not perform perturbation on this state". The code now raises an error on near-zero overlap instead of returning a value. [PR #3316](https://github.com/pyscf/pyscf/pull/3316), [PR #3404](https://github.com/pyscf/pyscf/pull/3404)

---

## Confirms / contradicts group notes

- **Confirms "PySCF `ipccsd_star` silently drops near-degenerate roots".** The code logs a WARN and skips the star correction for unmatched roots; it is not fully silent if you grep. PRs #3316 (included in v2.14.0) and #3404 (master only, GCCSD) fixed the pairing, so fewer roots should drop. Re-test before relying on the old workaround.
- **Confirms "ask for more roots / user guesses / separate by symmetry".** This is the developers' own order of fixes (#59, #809), with more guesses and preconverged singles tried *before* more roots.
- **Partly contradicts "always `EOM_DAVIDSON_CONVERGENCE 7`".** The manual says to use the default (5) for ordinary EOM. Our CAP finding is consistent with #59 (tighter = more iterations) but is not documented for CAP by Q-Chem. Keep it as a group rule for complex EOM only, and also set `EOM_DAVIDSON_THRESHOLD` to match, as the manual advises.
- **Confirms "frozen core: freeze only true core".** The FNO thread (#76) shows truncating the virtual space can remove Rydberg and EE states. That is a separate mechanism from frozen core, but the same lesson.
- **Confirms "identify roots by character, not ranking".** Developers say to use NTOs (#79) and R1²/R2² (#1031). In PySCF, `qpwt` plays the role of R1², but its value depends on normalization (#541).
- **Confirms "raw CAP energies are not physical / deperturb".** The manual turns `CC_EOM_PROP` on for the first-order correction. Burth et al. show two η-minima for N2⁻, which supports the group's "a plateau does not prove a resonance" caution.
- **Confirms "CC_TRANS_PROP needed for oscillator strengths"** (#1031). PySCF EOM-EE oscillator strengths exist only on master after 2026-10-11 (#3480).
- **Adds to "Q-Chem scratch":** silent deaths are often the Slurm OOM killer or a bad disk (#2956, #1461). Check the scheduler log before changing EOM settings.
- **"Mixed BASIS must list every atom":** also note that `BASIS = MIXED` turns symmetry off, so per-irrep `XX_STATES` arrays fail (#171). Use `GEN` when every atom of an element gets the same basis.

---

## Open questions / could not verify

- **CAP + DIP in 6.4 or 7.0:** whether CS/CAP-EOM-DIP-CCSD exists there (forum #3172 is unanswered).
- **EOM-EE-CCSD reference value:** I did not find a tabulated EOM-EE-CCSD value for water 1B1 in aug-cc-pVDZ. The ~0.1 eV agreement with exFCI is (unverified).
- **PySCF EOM-EE oscillator strengths:** whether the feature reaches a tagged release (v2.15?) is (unverified). Until then, install from master.
- **Default `EOM_DAVIDSON_THRESHOLD` in 6.4:** its value was lost in text extraction (unverified). Read the manual page directly.
- **CAP in PySCF:** PySCF has no built-in CAP-EOM-CC. The usual route is to build the CAP matrix externally (e.g. pyopencap) and project it onto EOM states (unverified; not researched here).
- **Q-Chem 7.0 manual:** section numbers changed (7.9.x). I did not check whether any EOM keyword defaults changed in 7.0.
