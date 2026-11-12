# Building and running a DIM model: the full recipe

The detailed notes behind the `dim` skill. These notes come from one project: an Ar 3s hole in a 658-atom Ar(111) slab next to a water molecule, extended to the Ar 3p hole. Validation numbers: `validation.md`. Excitons: the `di-dim` skill.

## 1. When DIM is the right tool

- **Good fit:** one hole shared among many identical, weakly bound atoms (rare-gas clusters, surfaces, solids), where you need picoseconds of dynamics for hundreds of atoms. The basis is "carrier on atom K", built from diatomic curves.
- **Why not ab initio dynamics here:** SA-CASSCF on 17 atoms took 35–40 min per step and its cc-pVDZ polarization was too small to place the sites correctly. DFT- and CASSCF-Ehrenfest collapsed a water onto the Ar⁺ (O–Ar 0.5–1.5 Å) through self-interaction error. DIM has no self-interaction (one carrier in a site basis) and runs at seconds per step.
- **Poor fit:** covalent systems; significant charge transfer onto a molecule (check its EOM weight; it was ≤ 3.4 % for Ar⁺/water at 2.5 Å); several holes at once unless you build a two-hole extension the same way (pair terms plus screening) and validate it.

## 2. Building the Hamiltonian

- **Site basis.** s-hole: one state per atom (spherical). p-hole: three spatial states per atom, and spin-orbit makes it 6 spin-orbitals per atom (complex H). Excitons need their own construction (`di-dim`). The basis is strictly diabatic (geometry-independent), so there are no derivative couplings in the site basis.
- **Diagonal (s-hole):** `H_KK = Σ_pairs V_n + Σ_{j≠K} [V_s(R_Kj) − V_n(R_Kj)] + [E_pol(K) − E_pol(0)] + (molecule terms)`. **Off-diagonal:** `H_KL = W(R_KL)`, with `V_s = ½(V_g + V_u)` and `W = ½(V_g − V_u)` from the ion-dimer g/u curves.
- **Get the sign of W right.** For a rare-gas hole the u state is the bound one (Ar₂⁺ ground state ²Σ_u⁺), so `H_KL = +W > 0` and the hole sits at the **lowest** eigenvalue. On an fcc lattice that is the −4W band edge, which is flat (frustrated lattice; Ar₃ levels 0, 0, 3W): expect near-degenerate states, track states by overlap and use overlap-based couplings.
- **p-holes:** rotate the Σ and Π dimer curves into the lab frame for each pair (Slater–Koster style), then add atomic spin-orbit in the site basis. Check the atomic limit (Ar⁺ ²P splitting 0.177 eV) and that a dimer reproduces the Hund's case (c) curves exactly.
- **Pair curves:** multireference CI with a size-extensivity correction (MRCI-ACPF or MRCI+Q), aug-cc-pVTZ, with spin-orbit where it matters. Check spectroscopic constants (Rₑ, Dₑ) against the literature. Take the neutral pair potential from an accurate published curve.
- **Polarization: many-body, not pairwise.** Remove the induction tail from the ion pair curve (`V_s = V₊ + C₄f₄/R⁴`) and replace it with self-consistent Thole-damped induced dipoles on every atom (μ = α[E⁰ + Tμ]), re-solved for each hole site at each step. Pairwise induction over-penalized surface sites (154/193 meV against EOM 94/109; many-body gave 95/113). Use the experimental polarizability (Ar 1.64 Å³; the aug-cc-pVDZ value 1.45 Å³ only for like-for-like checks against aDZ EOM). Thole a = 0.39.
- **Don't double count:** the two-body limit of the induced-dipole model must reproduce the ab initio tail exactly; test it on the dimer.

## 3. Adding a molecule (e.g. water)

- **Long range, no fitting:** point charges with the gas-phase dipole plus a polarizability in the induced-dipole set. This is standard ion–molecule physics and should pass blind tests on its own.
- **Short range: ab initio, not fitted walls.** Take ion···molecule and neutral···molecule pair terms from counterpoise-corrected dimer scans (several orientations, 2.5–12 Å). A fitted short-range wall shifted the water's equilibrium height by 0.2 Å and gave a trap 11–38 meV too deep before counterpoise. Fit only inside the region no blind test covers, and flag every fitted parameter.
- **Rigid molecule** is justified when its vibrations are far above every relevant scale (water: 10–30×), and it avoids zero-point-energy leakage into soft modes. Check the static distortion in the ion's field (< ~20 meV).

## 4. Numerics every DIM code must pass

- A dimer reproduces its input curves exactly (all states, all orientations, with spin-orbit).
- H is Hermitian; diabatic states never get reassigned across frames (count reassignments).
- Analytic gradients match finite differences (≤ 1e-5 eV/Å typical), including frozen atoms and molecule rigid-body rows.
- Energies are stated relative to a defined zero. Model-internal energies are often not absolute IPs: anchor to experimental fragment IPs if you need absolute numbers.

## 5. Validation checklist (blind where possible)

Write the DIM number down **before** looking at the reference. Mark each item justified / bracket / not yet. The detailed list with target numbers is in `validation.md`.

1. Site energies and couplings against EOM-IP-CCSD on 5–20-atom clusters, same basis as the reference: aim for 1–5 meV. Couplings: W at the lattice distance (Ar 3s: 18.0 vs EOM 18.1–18.8 meV).
2. Molecule shifts at several distances **and orientations**: a sign flip between orientations (H-up vs H-down water) tests the whole charge distribution, not only the dipole.
3. Large-system physics: the bulk polarization energy of one charge against experiment (Ar ≈ 1.0 eV), two-charge screening against ΔMP2, small-trimer minima (linear Ar₃⁺) against higher-level theory.
4. Slab size: converge the polarization (finite slab plus a per-site correction to a larger slab).
5. Triples: DIM fitted to EOM-CCSD inherits its level; state a bracket (Ar: offsets ×1–1.3).

## 6. Running dynamics on DIM

- **Algorithm:** CSDM (Ehrenfest force with decay of mixing) handles a dense, flat band without the active-state/wavefunction mismatch fewest-switches showed (2–3× for delocalized holes). Run FSSH-EDC as a comparison. Report **wavefunction populations**, never FSSH active-state fractions. SHARC settings, the CSDM force patch and drift checks: `sharc`.
- **Finite hole region:** propagate in sites near the region of interest. Report **both** a reflecting edge and an absorbing edge (a non-Hermitian term, validated against exact non-Hermitian propagation). Absorbed weight means "left the region", never decay. With an absorber E_tot is not conserved by design.
- **Mobile region:** only atoms near the action move; the rest stay in the Hamiltonian, frozen. Make the mobile region bigger than the distance the carrier travels (a 3s hole outran a 46-atom region), and check that the frozen boundary does not distort the result (phonons reflect there).
- **Initial conditions:** Wigner sampling of the neutral (zero point), then vertical ionization. Soft, anharmonic molecule orientations need Monte Carlo on the real surface; check the orientation populations against an independent estimate and reweight if they differ.
- **Decay (ICD, ETMD) as post-processing:** S(t) = exp[−∫Γ(t)dt/ħ] with Γ = Σ_K P_K Γ_K from wavefunction populations, valid while Γ ≪ W. Until widths are calibrated, show results as a function of the width.
- **Cost:** dense propagation scales as (states)³ per step. Sparse Krylov propagation is fine; dynamics on Ritz states is not a published scheme, so use it only as a validated size check.

## 7. Pitfalls

- Wrong sign of W: the carrier sits at the wrong band edge and everything downstream is off.
- Pairwise polarization in a solid: surface sites too high by 40–60 %.
- A parameter file swap that silently drops a fitted term (check the term is non-zero at runtime).
- Model energy columns that look like IPs but are not (constant offsets from the neutral term).
- Reading self-trapping from a reflecting-edge run: returned density can look like trapping.

## 8. Not verified yet

- Whether a single published reference contains self-consistent many-body induced dipoles for Rg_n⁺ DIM (Amarouche, Durand & Malrieu 1988 is on Xe_n⁺; its polarization content is unchecked).
- Langevin (stochastic) boundaries instead of a frozen outer region.

Sources: Ellison, JACS 85, 3540 (1963); Kuntz & Valldorf, Z. Phys. D 8, 195 (1988); Bonhommeau, Halberstadt & Buck, Int. Rev. Phys. Chem. 26, 353 (2007); Zhu, Nangia, Jasper & Truhlar, JCP 121, 7658 (2004) (CSDM); Carof, Giannini & Blumberger, JCP 147, 214113 (2017); Thole, Chem. Phys. 59, 341 (1981); group validation notes (2026).
