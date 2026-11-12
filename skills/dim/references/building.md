# Building and running a DIM model: the full recipe

The detailed notes behind the `dim` skill. These notes come from one project: an Ar 3s hole in a 658-atom Ar(111) slab next to a water molecule, extended to the Ar 3p hole. Validation numbers: `validation.md`. Excitons: the `di-dim` skill.

## 1. When DIM is the right tool

- **Good fit:** one hole shared among many identical, weakly bound atoms (rare-gas clusters, surfaces, solids), where you need picoseconds of dynamics for hundreds of atoms. The basis is "carrier on atom K", built from diatomic curves.
- **Why not ab initio dynamics here:** SA-CASSCF on 17 atoms took 35–40 min per step and its cc-pVDZ polarization was too small to place the sites correctly. DFT- and CASSCF-Ehrenfest collapsed a water onto the Ar⁺ (O–Ar 0.5–1.5 Å) through self-interaction error. DIM has no self-interaction (one carrier in a site basis) and runs at seconds per step.
- **Poor fit:** covalent systems; significant charge transfer onto a molecule (check its EOM weight; it was ≤ 3.4 % for Ar⁺/water at 2.5 Å); several holes at once unless you build a two-hole extension the same way (pair terms plus screening) and validate it.

## 2. Building the Hamiltonian

- **Site basis.** s-hole: one state per atom (spherical). p-hole: three spatial states per atom, and spin-orbit makes it 6 spin-orbitals per atom (complex H). Excitons need their own construction (`di-dim`). The basis is strictly diabatic (geometry-independent), so there are no derivative couplings in the site basis.
- **Diagonal (s-hole):** `H_KK = Σ_pairs V_n + Σ_{j≠K} [V_s(R_Kj) − V_n(R_Kj)] + [E_pol(K) − E_pol(0)] + (molecule terms)`. **Off-diagonal:** `H_KL = W(R_KL)`, with `V_s = ½(V_g + V_u)` and `W = ½(V_g − V_u)` from the ion-dimer g/u curves (V_s here is the raw average; the polarization step below replaces it with an induction-stripped curve V_s⁰).
- **Get the sign of W right: it follows orbital parity, not "u is bound".** The hopping is ½(V_sym − V_anti), where V_sym is the dimer state built from the *symmetric* combination of the two site functions. For s-sites the symmetric combination s_A + s_B is g, so `W = ½(V_g − V_u)`; the bound hole state is u (²Σ_u⁺), so W > 0 and the hole sits at the **lowest** eigenvalue. For p-sites in a common lab frame the symmetric combination is u (p_zA + p_zB is σ_u, p_xA + p_xB is π_u), so the blocks are `½(V_Σu − V_Σg)` (< 0 for Ar⁺, ²Σ_u⁺ bound) and `½(V_Πu − V_Πg)` (> 0 for Ar⁺, since ²Π_g lies below ²Π_u). The two blocks have opposite sign, and that relative sign is physical, not a convention. The same rule holds for any odd-parity site state (Ar 3p⁵4s: `di-dim`). Using the s-rule for p-sites flips both blocks. On an fcc lattice with s-hopping W > 0 the hole sits at the −4W band edge, which is flat along X–W (frustrated lattice; equilateral Ar₃ levels −W, −W, +2W): expect near-degenerate states, track states by overlap and use overlap-based couplings.
- **p-holes:** rotate the **spin-free** Σ and Π dimer curves into the lab frame for each pair (Slater–Koster style, signs as above), then add a constant atomic spin-orbit ζ in the site basis. Check the atomic limit (Ar⁺ ²P splitting 0.177 eV). Two separate dimer checks: (i) the code reproduces the case (c) curves of its own spin-free + atomic-ζ model exactly (an implementation test); (ii) those model curves against independent ab initio spin-orbit curves (a physics test of the constant-ζ approximation). If you only have spin-orbit-coupled ab initio curves, invert the two-state case (c) model to get effective spin-free curves first (Cohen & Schneider, JCP 61, 3230 (1974); check the reference) and say so.
- **Pair curves:** multireference CI with a size-extensivity correction (MRCI-ACPF or MRCI+Q), aug-cc-pVTZ, spin-free (spin-orbit enters only through the atomic ζ above). Check spectroscopic constants (Rₑ, Dₑ) against the literature. Take the neutral pair potential from an accurate published curve.
- **Polarization: many-body, not pairwise.** Remove the induction tail from the ion pair curve (`V_s⁰ = V_s + C₄f₄/R⁴`, used in place of V_s on the diagonal) and replace it with self-consistent Thole-damped induced dipoles on every atom (μ = α[E⁰ + Tμ]), re-solved for each hole site at each step. Pairwise induction over-penalized surface sites (154/193 meV against EOM 94/109; many-body gave 95/113). Use the experimental polarizability (Ar 1.64 Å³; the aug-cc-pVDZ value 1.45 Å³ only for like-for-like checks against aDZ EOM). Thole damping in the AMOEBA exponential form (λ₃ = 1 − exp(−a u³) on the 1/r³ term and λ₅ = 1 − (1 + a u³) exp(−a u³) on the 3rr/r⁵ term of the dipole tensor, u = r/(α_iα_j)^{1/6}) with a = 0.39 (Ren & Ponder 2003); a = 0.39 in a different damping form is far too strong, so name the form. Putting the full localized-hole E_pol(K) on each diagonal and nothing off-diagonal assumes the electrons' polarization follows the hole instantly (standard since Amarouche, Durand & Malrieu 1988); say so, because a delocalized hole polarizes its surroundings less than Σ_K |c_K|² E_pol(K).
- **Don't double count:** the two-body limit of the induced-dipole model must reproduce the ab initio tail exactly; test it on the dimer.

## 3. Adding a molecule (e.g. water)

- **Long range, no fitting:** point charges with the gas-phase dipole plus a polarizability in the induced-dipole set. This is standard ion–molecule physics and should pass blind tests on its own.
- **Short range: ab initio, not fitted walls.** Take ion···molecule and neutral···molecule pair terms from counterpoise-corrected dimer scans (several orientations, 2.5–12 Å). A fitted short-range wall shifted the water's equilibrium height by 0.2 Å and gave a trap 11–38 meV too deep before counterpoise. Fit only inside the region no blind test covers, and flag every fitted parameter.
- **Rigid molecule** is justified when its vibrations are far above every relevant scale (water: 10–30×), and it avoids zero-point-energy leakage into soft modes. Check the static distortion in the ion's field (< ~20 meV).

## 4. Numerics every DIM code must pass

- A dimer reproduces its input curves exactly (all states, all orientations, with spin-orbit).
- **The dimer cannot test the overall sign of W**: flipping every hopping sign is a gauge change on two sites (on any bipartite graph) and leaves the energies unchanged. The overall sign shows only in odd rings. Check an equilateral trimer (s-hopping W > 0: −W, −W, +2W, lowest level doubly degenerate; wrong sign: non-degenerate lowest level at −2|W|) and a tetrahedron (−W ×3, +3W vs −3W, +W ×3), against EOM-CC. For p-sites compare the spin-free level pattern and energies, not just the lowest degeneracy, and note that with spin-orbit on every hole level is a Kramers doublet. A *relative* Σ/Π sign error is different: with atomic spin-orbit on it changes the dimer's case (c) levels (~30 meV in a test), so the dimer test with spin-orbit does catch it.
- H is Hermitian; diabatic states never get reassigned across frames (count reassignments).
- Analytic gradients match finite differences (≤ 1e-5 eV/Å typical), including frozen atoms and molecule rigid-body rows.
- Energies are stated relative to a defined zero. Model-internal energies are often not absolute IPs: anchor to experimental fragment IPs if you need absolute numbers.

## 5. Validation checklist (blind where possible)

Write the DIM number down **before** looking at the reference. Mark each item justified / bracket / not yet. The detailed list with target numbers is in `validation.md`.

1. Site energies and couplings against EOM-IP-CCSD on 5–20-atom clusters, same basis as the reference: aim for 1–5 meV. Couplings: W at the lattice distance (Ar 3s: 18.0 vs EOM 18.1–18.8 meV).
2. Molecule shifts at several distances **and orientations**: a sign flip between orientations (H-up vs H-down water) tests the whole charge distribution, not only the dipole.
3. Large-system physics: the bulk polarization energy of one localized charge against experiment (Ar ≈ 1.0 eV from Ar 2p core-ionization relaxation, Wurth et al., PRB 47, 6697 (1993); a core hole is localized, so no bandwidth correction applies. Don't compare with the valence solid-minus-atom ionization shift, which also contains half the 3p hole bandwidth), two-charge screening against ΔMP2, small-trimer minima (linear Ar₃⁺) against higher-level theory.
4. Slab size: converge the polarization (finite slab plus a per-site correction to a larger slab).
5. Triples: DIM fitted to EOM-CCSD inherits its level; state a bracket (Ar: offsets ×1–1.3).

## 6. Running dynamics on DIM

- **Algorithm:** CSDM (Ehrenfest force with decay of mixing) handles a dense, flat band without the active-state/wavefunction mismatch fewest-switches showed (2–3× for delocalized holes). Run FSSH-EDC as a comparison. Report **wavefunction populations** as the observable. Show FSSH active-state fractions next to them only as a consistency diagnostic (for delocalized holes they disagreed by 2–3×). SHARC settings, the CSDM force patch and drift checks: `sharc`.
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
