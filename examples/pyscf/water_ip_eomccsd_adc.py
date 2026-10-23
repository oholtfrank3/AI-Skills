"""Ionization energies of water three ways: Koopmans (HF), EOM-IP-CCSD, IP-ADC(2) and IP-ADC(3).

Run: python water_ip_eomccsd_adc.py   (about a minute on a laptop)
Expected (PySCF 2.9, cc-pVDZ, geometry below), lowest IP in eV:
  Koopmans 13.419, EOM-IP-CCSD 11.800, IP-ADC(2) 10.980, IP-ADC(3) 12.194  (1b1, then 3a1, 1b2).
Experiment (vertical): 12.62 eV. cc-pVDZ is too small for quantitative IPs; use aug-cc-pVTZ for real work.
Skills: eom-cc (identify roots by character, check R1/spectroscopic factor), pyscf.
"""
from pyscf import gto, scf, cc, adc

HA2EV = 27.211386

mol = gto.M(
    atom="""O 0.000 0.000 0.117
            H 0.000 0.757 -0.469
            H 0.000 -0.757 -0.469""",
    basis="cc-pvdz", verbose=0)
mf = scf.RHF(mol).run()
print(f"RHF energy            {mf.e_tot:.6f} Eh")
print("Koopmans IPs (eV)    ", [round(-e * HA2EV, 3) for e in mf.mo_energy[mol.nelectron // 2 - 3:mol.nelectron // 2][::-1]])

mycc = cc.CCSD(mf).run()
e_ip, _ = mycc.ipccsd(nroots=3)
print(f"CCSD energy           {mycc.e_tot:.6f} Eh")
print("EOM-IP-CCSD IPs (eV) ", [round(e * HA2EV, 3) for e in e_ip])

for method in ("adc(2)", "adc(3)"):
    myadc = adc.ADC(mf)
    myadc.method = method
    myadc.method_type = "ip"
    e, v, spec, x = myadc.kernel(nroots=3)
    print(f"IP-{method.upper():7s} IPs (eV)  ", [round(x_ * HA2EV, 3) for x_ in e],
          " spec. factors", [round(s, 2) for s in spec])
