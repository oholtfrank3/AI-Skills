"""Ne2 inner-valence (2s) ionization with EOM-IP-CCSD: the starting point for an ICD width.

The 2s holes sit near 48 eV, far above the 2p holes, so the default Davidson guess misses them.
Here `koopmans=True` with one root per occupied orbital reaches them.
Run: python ne_dimer_ip_2s.py   (a few minutes; aug-cc-pVDZ)
Expected (PySCF 2.9, R = 3.1 Å): six 2p IPs at 21.03–21.26 eV and the 2s pair at 48.348 and 48.356 eV (8 meV apart).
Experiment: Ne 2s^-1 about 48.5 eV (atom). The ICD width itself needs CAP-EOM in Q-Chem (examples/qchem).
Skills: eom-cc §2 (inner-valence roots), troubleshooting reference for Davidson problems.
"""
import numpy as np
from pyscf import gto, scf, cc

HA2EV = 27.211386

mol = gto.M(atom="Ne 0 0 0; Ne 0 0 3.1", basis="aug-cc-pvdz", verbose=0)
mf = scf.RHF(mol).run()
nocc = mol.nelectron // 2
print(f"RHF energy {mf.e_tot:.6f} Eh")
print("occupied orbital energies (eV):", np.round(mf.mo_energy[:nocc] * HA2EV, 2))

mycc = cc.CCSD(mf, frozen=2).run()  # freeze the two Ne 1s orbitals (true core only)
# koopmans=True takes one root per occupied orbital, so asking for all of them reaches the 2s pair.
nocc_act = nocc - 2
e_ip, v_ip = mycc.ipccsd(nroots=nocc_act, koopmans=True)
print("EOM-IP-CCSD IPs (eV):", np.round(np.sort(e_ip) * HA2EV, 3))
