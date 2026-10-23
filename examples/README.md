# Example scripts

Small, working calculations to copy from. Each one says what it computes, how long it takes, and the numbers you should get, so a first run also checks your setup. Run the matching checker on the output (`scripts/check_qchem_output.py`, `scripts/check_sharc_lis.py`) before trusting anything.

| Method | Code | System | File | Expected | Tested |
|---|---|---|---|---|---|
| HF, EOM-IP-CCSD, IP-ADC(2), IP-ADC(3) | PySCF | water, cc-pVDZ | [pyscf/water_ip_eomccsd_adc.py](pyscf/water_ip_eomccsd_adc.py) | first IP: Koopmans 13.42, EOM-IP-CCSD 11.80, ADC(2) 10.98, ADC(3) 12.19 eV (expt. 12.62) | PySCF 2.9, laptop, 1 s |
| EOM-IP-CCSD, inner-valence (2s) holes | PySCF | Ne₂ at 3.1 Å, aug-cc-pVDZ | [pyscf/ne_dimer_ip_2s.py](pyscf/ne_dimer_ip_2s.py) | 2p IPs 21.03–21.26 eV; 2s pair 48.348 / 48.356 eV | PySCF 2.9, laptop, 2 s |

More starter calculations with reference values (Psi4 SAPT, CP2K water, pyopencap N₂⁻, TiDES water spectrum) are listed in `skills/troubleshooting/references/*.md`.

**Adding an example:** keep it small (minutes on a laptop or one short PACE job), put the expected numbers and the code version in the header, and add a row here.
