# Example scripts

Small, working calculations to copy from. Each one says what it computes, how long it takes, and the numbers you should get, so a first run also checks your setup. Run the matching checker on the output (`scripts/check_qchem_output.py`, `scripts/check_sharc_lis.py`) before trusting anything.

| Method | Code | System | File | Expected | Tested |
|---|---|---|---|---|---|
| HF, EOM-IP-CCSD, IP-ADC(2), IP-ADC(3) | PySCF | water, cc-pVDZ | [pyscf/water_ip_eomccsd_adc.py](pyscf/water_ip_eomccsd_adc.py) | first IP: Koopmans 13.42, EOM-IP-CCSD 11.80, ADC(2) 10.98, ADC(3) 12.19 eV (expt. 12.62) | PySCF 2.9, laptop, 1 s |
| EOM-IP-CCSD, inner-valence (2s) holes | PySCF | Ne₂ at 3.1 Å, aug-cc-pVDZ | [pyscf/ne_dimer_ip_2s.py](pyscf/ne_dimer_ip_2s.py) | 2p IPs 21.03–21.26 eV; 2s pair 48.348 / 48.356 eV | PySCF 2.9, laptop, 2 s |
| RHF, UHF, CCSD bond-breaking curve | Psi4 | H₂, STO-3G, 0.25–4 Å | [psi4/h2_dissociation.py](psi4/h2_dissociation.py) | RHF = UHF up to ~1.2 Å; at 4 Å RHF −0.6150, UHF and CCSD −0.9332 Eh | Psi4 1.11, laptop, 10 s |
| Optimization + harmonic frequencies, HF/MP2/CCSD(T) | Psi4 | water, cc-pVDZ (cc-pVTZ optional) | [psi4/h2o_opt_freq.py](psi4/h2o_opt_freq.py) | CCSD(T)/cc-pVDZ 1690.7 / 3820.3 / 3926.4 cm⁻¹ | Psi4 1.11, laptop, 20 s |
| AIMD, PBE-D3, NVT 300 K | CP2K | excess proton in 64 waters (190 atoms, periodic) | [cp2k/excess_proton_water/](cp2k/excess_proton_water/) | E_pot(0) −1086.04996 Eh; conserved quantity drifts 0.5 mEh in 190 fs | CP2K 2022.1, PACE 24 cores, ~4 s/step (original outputs, not re-run) |

More starter calculations with reference values (Psi4 SAPT, CP2K water box, pyopencap N₂⁻, TiDES water spectrum) are listed in `skills/troubleshooting/references/*.md`.

**Adding an example:** keep it small (minutes on a laptop or one short PACE job), put the expected numbers and the code version in the header, and add a row here.

The Psi4 and CP2K examples are adapted from the STACC summer-school tutorials kept in the group Dropbox (Psi4 tutorials by C. Sargent, J. Hale, C. Renfro and D. Sherrill).
