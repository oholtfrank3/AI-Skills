---
name: troubleshooting
description: What to do when a calculation fails, crashes, does not converge, is missing roots or states, prints an unfamiliar error or keyword, gives results that look wrong, or you are unsure how a code (Q-Chem, PySCF, Psi4, CP2K, pyopencap/OpenCAP, SHARC, TiDES) handles something. Search the official docs, then the code's forum and issue tracker, then the literature, BEFORE guessing a fix or submitting a test job. Includes per-code reference files with documentation links, starter calculations and known issues collected from forums. Also use when someone asks for a simple test calculation to check their setup.
---

# Troubleshooting: search first, then fix (Kretchmer group notes)

Every wrong guess on PACE costs a 2–5 hour job and someone's afternoon. Most problems have already been hit by someone else and answered in a manual, a forum thread or a paper. Look there first.

## 1. Search order

When you do not know the answer for certain:

1. **The group's own notes:** the skill for that code (`eom-cc`, `sharc`, `pace-slurm`, …) and its `references/`.
2. **This skill's reference file for that code** (§3). Check its "Known issues and fixes" list for the symptom.
3. **The official manual** for the code version actually installed. Check the version first: keywords and defaults change between releases.
4. **The code's forum and issue tracker**, searched with the exact error text in quotes, then with the keyword names:
   - Q-Chem: talk.q-chem.com
   - PySCF: github.com/pyscf/pyscf issues and discussions
   - OpenCAP: github.com/gayverjr/opencap issues
   - SHARC: github.com/sharc-md/sharc issues; sharc-md.org
   - General: Matter Modeling Stack Exchange
5. **The literature:** the method paper and any benchmark paper that ran the same kind of system.
6. **Shipped samples and tests:** run the code's own example input closest to your case before changing your input. A sample that works narrows the problem to your input.

Only after that, propose a fix. Say where it came from: "The Q-Chem manual says…", "A forum thread from 2023 had the same error; the fix was…", or "I couldn't find this anywhere, so this is my best guess."

## 1b. Check outputs with the scripts first

For "did my job work?" questions, run the plugin's checkers before reading logs by hand: `scripts/check_qchem_output.py` (Q-Chem) and `scripts/check_sharc_lis.py` (SHARC). Then record the outcome with `/compchem:log-calc`.

## 2. Talking to the user about a problem

The user may be new to this. Keep it calm and short:

- Say what went wrong in one plain sentence ("The calculation stopped because it couldn't find enough excited states").
- Say what you found and where, in one or two sentences.
- Propose one next step and ask before running it. If it needs a PACE job, follow `pace-slurm` §0. Ordered fix lists in the reference files are for you: give the user the first step that fits, not the whole list.
- End with one line naming the source: the group notes or reference file, the manual section, or the forum thread (with link). If you are going on general knowledge because nothing was found, say so.
- Do not paste whole error logs or long forum excerpts into chat. Quote the key line.

## 3. Reference files

Each file has official documentation links with keyword summaries, a few **starter calculations** (small test cases with a known answer, good for checking a new setup), and **known issues and fixes** gathered from forums and papers, with links and dates.

| Code | File |
|---|---|
| Q-Chem / PySCF EOM-CC and CAP-EOM | `references/qchem-pyscf-eomcc-cap.md` |
| PySCF (SCF/DFT, CASSCF, geometry, performance) | `references/pyscf.md` |
| Psi4 (SAPT, counterpoise, CBS) | `references/psi4.md` |
| CP2K (periodic DFT, AIMD) | `references/cp2k.md` |
| pyopencap / OpenCAP (projected CAP) | `references/pyopencap.md` |
| SHARC | `references/sharc.md` |
| TiDES and real-time TDDFT | `references/tides.md` |

**Starter calculations come first.** Before a new person's first real job, or on a new machine or code version, run the closest starter calculation and compare it to the reference value. It takes minutes and catches most setup problems.

## 4. Grow the backlog

When a problem gets solved, offer once, in one line: "Want me to save this fix to the group's backlog so the next person finds it?" On yes, follow `/compchem:log-fix`. It drafts a symptom → cause → fix entry, shows it to the user, and files it as a `known-issue` issue on the plugin repo. Do not edit the installed plugin's files directly. A maintainer folds the issues into the reference files and skills with `/compchem:merge-fixes`.

Each reference file records the date it was researched. If that is more than about six months ago, or the installed code version is newer, search again before trusting it.
