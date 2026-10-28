"""Water geometry and harmonic frequencies at HF, MP2 and CCSD(T) in Psi4.

What it shows: how the bond length, angle and frequencies change with the
method and the basis. HF overestimates the stretches by ~7 %, because it
lacks electron correlation; MP2 and CCSD(T) are close to each other.

Run:  python h2o_opt_freq.py [basis]     (default cc-pvdz, ~20 s on a laptop;
      cc-pvtz is the original and takes a few minutes. CCSD(T) frequencies
      come from finite differences of gradients.)

Expected, cm^-1 bend / sym. stretch / asym. stretch (DF, frozen core):

  cc-pVDZ, Psi4 1.11 (tested here):
           HF      1775.7 / 4113.4 / 4212.1   r(OH) 0.9463 Å, HOH 104.66°
           MP2     1678.2 / 3850.5 / 3969.9   r(OH) 0.9650 Å, HOH 101.91°
           CCSD(T) 1690.7 / 3820.3 / 3926.4   r(OH) 0.9664 Å, HOH 101.92°
  cc-pVTZ, Psi4 1.3.2 (original STACC outputs, not re-run):
           HF      1752.8 / 4128.2 / 4228.3   r(OH) 0.9405 Å, HOH 106.00°
           MP2     1652.1 / 3855.7 / 3976.1   r(OH) 0.9591 Å, HOH 103.51°
           CCSD(T) 1669.0 / 3840.9 / 3945.5   r(OH) 0.9594 Å, HOH 103.58°

Psi4 1.3.2 gave the same cc-pVDZ frequencies to within 3 cm^-1.
Experimental fundamentals are 1595 / 3657 / 3756 cm^-1. They include
anharmonicity, so even exact harmonic frequencies sit ~3-5 % higher.
Check: three real frequencies and no imaginary ones (an imaginary mode means
the optimization did not reach a minimum).

Adapted from the STACC Psi4 tutorials (C. Sargent, J. Hale, C. Renfro,
D. Sherrill).
"""
import sys
import psi4

basis = sys.argv[1] if len(sys.argv) > 1 else "cc-pvdz"
psi4.set_memory("4 GB")
psi4.set_output_file(f"h2o_opt_freq_{basis}.out", False)
psi4.set_options({"basis": basis, "scf_type": "df", "mp2_type": "df",
                  "cc_type": "df", "freeze_core": True})

for method in ["scf", "mp2", "ccsd(t)"]:
    # z-matrix: one O-H length and the angle are optimized; symmetry kept
    mol = psi4.geometry("""
    0 1
    H
    O 1 oh
    H 2 oh 1 hoh

    oh = 0.96
    hoh = 104.5
    """)
    psi4.optimize(method)
    # dertype=1: CCSD(T) frequencies from gradients (no analytic Hessian)
    e, wfn = psi4.frequency(method, dertype=1, return_wfn=True)
    freqs = wfn.frequencies().to_array()
    print(f"{basis} {method:8s} r(OH) = {mol.get_variable('oh'):.4f} Å  HOH = {mol.get_variable('hoh'):.2f}°  "
          f"freqs = {', '.join(f'{f:.1f}' for f in freqs)} cm^-1")
    psi4.core.clean()
