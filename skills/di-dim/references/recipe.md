# Di-DIM recipe: Rydberg excitons in rare-gas clusters and solids

How to build a DIM model for a neutral np⁵(n+1)s exciton (Ar 3p⁵4s here) and what went wrong on the way. From the group's 2026 work, which follows the Di-DIM construction of Dhiman & Gervais but computes every input curve instead of fitting any. Numbers marked PRELIMINARY are group results not yet published; use them as orientation, not as references.

## 1. What changes from a hole model

- **Basis:** one excited atom in a ground-state background. For 3p⁵4s each excited site carries the three p-hole orientations × {triplet, singlet}: 12 spin states per site (³P: 9, ¹P: 3). Spin-orbit is optional and goes in the site basis (constant ζ from the Ar⁺ ²P splitting, on the p hole only). Atomic check: with spin-orbit alone (no singlet–triplet exchange) the triplet gives ³P₂/³P₁/³P₀ = −ζ/2, +ζ/2, +ζ with degeneracies 5/3/1. With the full 12-state block, ³P₁ and ¹P₁ mix (intermediate coupling) and the levels must match the NIST values in §6 instead; the pure pattern then no longer holds.
- **Diabatic β states (only if you diabatize, §3):** one extra state per excited-site *pair* K–L closer than a cutoff (6 Å in the group code), the 4p-derived Σ state of Di-DIM's 4×4 pair block. It couples only to the Σ combination of that pair's two 4s sites. β is pair-centred, not atom-centred, so the usual DIM bookkeeping is not exact for it: it sees the rest of the cluster only through the neutral pair potential (state this assumption). That is why the count below is "12 per site plus one per close pair and spin".
- **Hamiltonian:** H = Σ_{A<B} H_AB − (M − 2) Σ_A H_A. The pair blocks come from the spin-free Ar₂* Σ/Π g/u curves (triplet and singlet), rotated into the lab frame as for a p-hole. The 3p⁵4s site state has odd parity like Ar⁺(3p⁵), so the hopping signs follow the p-hole parity rule (`dim` skill, `building.md` §2): Σ block ½(V_Σu − V_Σg), Π block ½(V_Πu − V_Πg). All other pairs use the neutral potential.
- **Cost:** 12 states per site plus the β states (one per close pair and spin), so dense propagation gets expensive fast; keep the excitation region to a few dozen sites and check region size.
- **No charge, so no ion-induced polarization.** Say explicitly which polarization terms apply to a neutral exciton (none in the group's model). That is a known gap: the cluster literature finds a large outward dipole on surface excimers.
- **Spin and selection rules:** only J = 1 states (³P₁, ¹P₁) are dipole-allowed. If energy transfer or emission matters, keep spin-orbit and J.
- **Long-range resonant transfer:** the J = 1 states also hop by dipole–dipole coupling falling as 1/R³. A rough estimate for ¹P₁ (f ≈ 0.2 at 11.8 eV) gives tens of meV at the nearest-neighbour distance, so it can't be dropped beyond the pair-curve range or the excitation region. Say which target state the model is built for: a small excitation region without spin-orbit is fine for the lowest triplet, not for the J = 1 band or emission.

## 2. Pair curves (the expensive, decisive part)

- **Method:** EOM-EE-CCSD with doubly augmented basis sets (d-aug-cc-pVTZ for the scan, d-aug-cc-pVQZ anchors). The atomic 4s level rose by 0.12 eV from daTZ to daQZ, while the relative curves changed by ≤ 4 meV at 3–3.8 Å and 16–23 meV at 2.4 Å. So compare curves relative to each basis's own asymptote.
- **Roots:** include the lowest (n+1)p Σ_g⁺/Σ_u⁺ states as well as all (n+1)s Σ/Π g/u. The 4s ³Σ_g⁺ state mixes strongly with a 4p Σ_g⁺ state below ~2.6 Å. This 4s/4p avoided crossing is what Di-DIM handles with a fitted "ad hoc" curve; computing the 4p partner removes the need for it.
- **Symmetry:** use D2h labels (z = axis: Σ_g⁺ → Ag, Σ_u⁺ → B1u, Π_g → B2g/B3g, Π_u → B2u/B3u) so states are assigned without guessing. Ask only for the roots you need per irrep: 6 roots × 8 irreps × 2 spins timed out, and 22 targeted roots were enough.
- **Q-Chem trap:** for Ar₂ with d-aug basis sets at R ≥ 3.5 Å, near-degenerate g/u orbitals come out mixed, "Irrep of orbital could not be determined" appears, and CCMAN2 silently falls back to C1. It then solves only the first entry of `EE_SINGLETS`/`EE_TRIPLETS` and can miss the lowest state. `USE_LIBQINTS` and a DFT pre-step did not fix it. Projecting the EOM Davidson onto each irrep in PySCF (symmetry-blocked RHF, amplitudes masked by orbital irrep) matched Q-Chem to 1e-4 eV where both worked.
- **Ground-state part of the excited curve:** use the accurate neutral curve + the EOM excitation energy, V*(R) = V_n(R) + ΔE_EOM(R). All the other pairs use V_n, and the diagonal subtracts V_n, so a pure EOM-CC excited curve (CCSD ground + excitation) leaves a spurious CCSD-minus-accurate long-range term in every excited pair. The two choices differed by 0.09 eV in De(Ar₂*) and ~200 cm⁻¹ in De(Ar₃*); report that as an error bar, not as a free choice.
- **Inner walls:** with no wall, a trimer collapsed during relaxation. Best: compute points in to ~2.0 Å. A continuation such as linear + the neutral curvature, then exponential, is a guess, not a fit-free result: flag it, and check that no trajectory or minimum samples it.

## 3. Diabatization of the s/p mixing (the choice that matters most)

Why it matters: the adiabatic 4s ³Σ_g⁺ pair curve is partly 4p at short range. A 4s-only site basis has no state to carry that 4p admixture, so the s/p-stabilized pair curves don't transfer correctly to clusters. Plain adiabatic DIM overbinds Ar₃* badly (De 700–1300 cm⁻¹ against CASPT2 340, HPP 290, Di-DIM 160). Diabatizing the 4s/4p Σ_g mixing fixes most of it, but the result depends on the criterion. Don't pick the criterion by matching a published number; benchmark it.

- **Criteria tried:** wavefunction-overlap propagation from a large-R reference, Mulliken s-character ratio, Löwdin. They gave mixing angles of 28° vs 54° at 2.4 Å and moved De by ±150 cm⁻¹. That spread is itself a warning: Mulliken and Löwdin populations are basis-dependent, and in a doubly augmented basis the diffuse functions on the two atoms are nearly linearly dependent (Reed, Weinstock & Weinhold, JCP 83, 735 (1985)). More robust choices to compare: ⟨r²⟩ or the quadrupole of the excited natural transition orbital, or projection onto the large-R atomic 4s and 4p states.
- **Benchmark that chose it:** linear Ar₃* (one excimer pair + a third atom at 2.6–10 Å, plus symmetric geometries), lowest triplet, EOM-EE-CCSD/d-aug-cc-pVTZ. DIM − EOM over 10 geometries (PRELIMINARY): Mulliken s-ratio MAE 17 meV (max 34); overlap 35 (121); none 60 (192); Löwdin 47 (85; also erratic, an N = 6 cluster came out unbound). The Mulliken criterion gave Ar₃* De = 238 cm⁻¹, inside the literature range. No continuous parameter was fitted, but the criterion was chosen as the best of four on this same set, so 238 cm⁻¹ is not an independent test. Validate on geometries not used for the choice (a bent trimer, Ar₄*), and report De for every criterion.
- **Known gap:** EOM finds a weak long-range attraction of the third atom (−12.5 meV at 3.2 Å after counterpoise; the raw value was −22.9 meV) that pairwise DIM misses. It is the same size as the differences between criteria, so the winner may partly be winning by error cancellation.
- **Checks still to do:** a population ratio fixes only the size of the mixing angle, not the sign of the diabatic coupling. Plot the diabats, their slopes and the coupling against R and check for kinks or sign jumps. Only the ³Σ_g⁺ channel was diabatized; the same core switch (a 4p electron on a ²Σ_u⁺ core dropping below 4s on ²Σ_g⁺) can occur in the Π channels with 4pπ. Check the Π curves for it, or state that it was found negligible.
- **Assumption to state:** the extra diabatic (β) state sees the rest of the cluster only through the neutral potential.

## 4. Numerical tests (all should pass before any physics)

- A dimer reproduces its input curves to machine precision, with and without diabatization.
- **Hopping sign:** a dimer can't test it (a global sign flip is a gauge change on two sites). Check an equilateral Ar₃* and a tetrahedral Ar₄* against EOM-EE-CCSD (degeneracy of the lowest levels).
- Gradients vs finite differences (< 1e-8 eV/Å achievable), with spin-orbit and diabatization switched on and off.
- Spin-orbit block Hermitian and rotation-invariant; atomic J levels and degeneracies correct.
- Region-size check: excitation region and mobile region enlarged → energies within ~10 meV.

## 5. Adding a molecule to an exciton model

- Neutral-exciton···molecule interactions are short-range and **anisotropic**. For Ar*(4s)···N₂ the Σ-like triplet goes from about +85 meV (side-on) to −94 meV (end-on) at 3.6 Å, while Π stays near-isotropic (PRELIMINARY). End-on it mixes with molecule states. A two-term Legendre form (V₀ + V₂P₂) was good to only 10–20 meV there.
- Check the pair model on an excimer + molecule geometry: the group's first N₂ model under-estimated the repulsion on Ar₂* by 1.5–3×.
- Counterpoise was negligible (≤ 0.6 meV) for the 4s states with N₂, but check it for each molecule.

## 6. What to compare with

Validation checklist for an exciton model (blind where possible; mark justified / bracket / not yet):
- Dimer limit, gradients, spin-orbit block, region size (§4).
- Site energies and transfer couplings vs EOM-EE-CCSD on small clusters; Ar₃* linear benchmark (§3).
- Atomic J levels with spin-orbit; Ar₂* Rₑ, Dₑ and emission; Ar₃* Dₑ vs CASPT2/HPP/Di-DIM.
- Exciton bulk and surface energies: this is where non-pairwise Rydberg repulsion shows up (the 4s orbital radius is comparable to the nearest-neighbour distance, so pairwise Pauli repulsion over-counts in the bulk). Bound it first, e.g. EOM on Ar₁₃* against the pairwise sum, before using the bulk and surface numbers below as validation.
- Say which polarization terms apply to a neutral carrier and which do not.

Reference values:

- Atomic 4s levels: ³P₂ 11.548, ³P₁ 11.624, ³P₀ 11.723, ¹P₁ 11.828 eV (check against NIST before citing).
- Ar₂* (³Σ_u⁺) Rₑ ≈ 2.4 Å (4.52 au in Di-DIM), excimer emission (M band) ≈ 9.7 eV in the solid, ~9.4 eV for small-cluster HPP triplets.
- Solid Ar: free excitons 12.06 / 12.24 eV, surface excitons ~11.7 / 11.9 eV (check before citing).
- Di-DIM lowest-isomer geometries and energies for N = 3–25 and 55–57 are in the authors' data repository (github.com/simul-md/Di-DIM); its PEC folder was empty in Nov 2026, so the curves themselves are not downloadable.

## 7. Dynamics on an exciton DIM

- Settings as for holes (`dim` skill and `sharc` skill, CSDM or single-state adiabatic NVE). Trapping can be very fast (tens to hundreds of fs), and some Wigner starts are already localized at t = 0 by zero-point motion: report the localization (IPR) at t = 0.
- Check the gap to the next state over the run. If it is small often, single-surface dynamics is not enough.
- Desorption of a surface excimer can take several ps. Run long enough (the group continued to 25 ps), and check region size (mobile region, number of excitation sites) before trusting lift-off statistics.

## Sources

- Dhiman & Gervais, Chem. Phys. Lett. (2026), doi:10.1016/j.cplett.2026.142825 (preprint arXiv:2409.06484): Di-DIM.
- Dhiman, Douady & Gervais, Mol. Phys. 120, e2049905 (2022): HPP for Ar_N excitons.
- Kuntz & Valldorf, Z. Phys. D 8, 195 (1988): DIM pair rotation.
- Group exciton DIM notes (Nov 2026, PRELIMINARY).
