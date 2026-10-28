"""H2 dissociation curve with RHF, UHF and CCSD in Psi4 (STO-3G).

What it shows: RHF goes wrong as the bond breaks (it forces both electrons
into one orbital, so it dissociates to H+ + H- mixtures), UHF fixes the energy
at long range by breaking spin symmetry, and CCSD (exact for two electrons)
is right everywhere.

Run:  python h2_dissociation.py     (psi4 from conda-forge; a few seconds)

Expected energies (Eh; Psi4 1.11, conda-forge, macOS laptop, ~10 s):

  R/Å    RHF            UHF            CCSD
  0.75  -1.1161753863  -1.1161753863  -1.1371213014
  1.00  -1.0661355662  -1.0661355662  -1.1011491705
  1.50  -0.9109520429  -0.9577019768  -0.9981224720
  2.00  -0.7839052320  -0.9372246391  -0.9486519416
  4.00  -0.6150178749  -0.9331661982  -0.9331703070

Checks: RHF = UHF up to ~1.2 Å (the Coulson-Fischer point), then UHF drops
below RHF. At 4 Å CCSD and UHF both approach 2 x E(H atom, STO-3G) =
-0.93316 Eh. PySCF with conventional integrals gives the same CCSD to 1e-5.
If UHF equals RHF at long range, the guess did not break symmetry: keep
guess_mix (and the GWH guess) on.

The original STACC run (Psi4 1.3.2) gave identical RHF/UHF and CCSD lower by
up to 1.5e-4 Eh; its input used Psi4's old Table class, which was removed,
so this is a modern rewrite.
Adapted from the STACC Psi4 tutorials (C. Sargent, J. Hale, C. Renfro,
D. Sherrill).
"""
import psi4

psi4.set_memory("2 GB")
psi4.set_output_file("h2_dissociation.out", False)
psi4.set_options({"basis": "sto-3g", "scf_type": "df", "freeze_core": True})

distances = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 4.0]
print(f"{'R/Å':>6} {'RHF':>15} {'UHF':>15} {'CCSD':>15}")
for r in distances:
    mol = psi4.geometry(f"""
    0 1
    H
    H 1 {r}
    symmetry c1
    """)
    psi4.set_options({"reference": "rhf", "guess": "sad", "guess_mix": False})
    e_rhf = psi4.energy("scf")
    e_ccsd = psi4.energy("ccsd")
    # UHF only breaks symmetry with a mixed (HOMO/LUMO-rotated) guess
    psi4.set_options({"reference": "uhf", "guess": "gwh", "guess_mix": True})
    e_uhf = psi4.energy("scf")
    print(f"{r:6.2f} {e_rhf:15.10f} {e_uhf:15.10f} {e_ccsd:15.10f}")
    psi4.core.clean()
