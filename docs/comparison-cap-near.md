# With and without the plugin: a CAP trajectory problem on Ne–Ar

*Recorded 2026-10-23.* The same three user messages were sent twice:

- **With the plugin:** Owen's real session, starting from `/compchem:start`. It is copied from the terminal. A few lines were cut off at the terminal edge; those spots are marked […].
- **Without:** Claude Code with the plugin off and skills blocked (`--disallowedTools Skill`), in an empty folder. This is roughly what a new account gets. Same model, same day.

The user's three messages:
1. "I am having an issue with some of my CAP results, where I don't see a clean U-turn, instead the values just bounce around in Re vs Im and there is no clear trend."
2. "I am running with the aug-cc-pVDZ basis for the argon neon dimer"
3. "full CAP-EOM-IP-CCSD in Q-Chem"

## Summary

| | Without the plugin | With the plugin |
|---|---|---|
| Length | 470–570 words per reply | about 250–350 words |
| Shape | a menu of 6–7 possible causes each turn | the 3 likely causes, then one question |
| Questions to the user | four things at once (state, η range, CAP settings, convergence) | one per turn ("projected or full CAP?") |
| Tight Davidson convergence (`EOM_DAVIDSON_CONVERGENCE 7`) | only "tighten it" in turn 3 | named first, with the group's finding that loose convergence moved widths by 20–135 % |
| Expected width for NeAr | "meV scale, tiny" | tens of meV: CAP-EOM-CCSD 37 meV vs 15–22 meV from other methods (arXiv:2305.10186) |
| Ghost / diffuse functions | generic even-tempered shells (divide the exponent by 2) | exponents matched to the outgoing electron's energy (group notes) |
| Group experience | none | "the same thing happened in the group's Ar–water runs" |
| Q-Chem CAP units | "as I remember it … verify in the manual" | not needed; it asks for the outputs instead |
| Next step | offers to write analysis scripts | run the group's output checker on the existing η scan first: no new jobs, no compute |
| Sources | one paper citation | says where each point comes from |

**What plain Claude does well:** solid textbook advice: track the root by overlap, use a log-spaced η grid and the corrected trajectory U = E − η·dE/dη, add diffuse shells. In turn 3 it also suggests a user guess on the Ne 2s orbital and requesting roots only in A1.

**What the plugin adds:** the group's own experience (what actually went wrong in our CAP runs), a sense of how big the answer should be, a beginner-friendly pace (one question at a time), and a free first step before any new PACE job.

---

## With the plugin

**User:** I am having an issue with some of my CAP results, where I don't see a clean U-turn, instead the values just bounce around in Re vs Im and there is no clear trend.

*(Claude loaded `compchem:troubleshooting` and ran 2 shell commands.)*

> That's a common CAP problem and usually has a clear cause. When the points scatter in the Re–Im plane, it normally means one of three things:
>
> 1. The wrong state is being followed. As η changes, the code jumps between neighbouring roots. Each jump moves the point somewhere new, so you get scatter where there should be a smooth curve.
> 2. The η values are spaced too widely, so the U-turn falls between two points and never shows up.
> 3. The state you're following isn't a real resonance, or, with projected CAP, the set of states you projected onto doesn't contain the decay channel. Then there is no U-turn to find. This is what happened in the group's Ar–water ICD/ETMD runs.
>
> What to check next depends on how you ran it, so one question first:
>
> Did you run projected CAP (pyopencap, or Q-Chem PROJ_CAP) or full CAP-EOM-CCSD in Q-Chem (COMPLEX_CCMAN with a scan over CAP_ETA)? Also tell me where the output files are, either in this folder or on PACE, so I can look at the trajectory myself.

**User:** I am running with the aug-cc-pVDZ basis for the argon neon dimer

> Thanks, the basis set is very likely the cause.
>
> aug-cc-pVDZ is probably too small for a CAP calculation on Ne–Ar. In Ne–Ar, a Ne 2s hole […] the released energy knocks an electron off the argon. To get a decay width, the basis has to describe that outgoing electron so the CAP has something to absorb. aug-cc-pVDZ has only one diffuse shell per angular momentum on each atom. With so little to work with, changing η just pushes a few artificial "continuum" states around, so the trajectory scatters with no U-turn.
>
> What our notes and the literature say:
>
> - The group's eom-cc notes say to add ghost centres (extra basis functions on an empty point) for CAP and ICD widths, with exponents matched to the energy of the outgoing electron rather than a generic diffuse set.
> - The NeAr benchmark paper (arXiv:2305.10186) used larger bases with extra diffuse functions […] CAP-EOM-CCSD gave 37 meV at 3.5 Å, against 15–22 meV from other methods. Expect a width of tens of meV. That is small enough that a poor basis easily drowns it out.
> - For projected CAP, if the projected states don't include the decay channel, […]. The same thing happened in the group's Ar–water runs.
>
> I'd do these in order:
> 1. Add a ghost atom at the Ne–Ar midpoint carrying a few extra diffuse s, p and d shells. Q-Chem's own CAP example does the same thing for N₂. Moving up to aug-cc-pVTZ on the atoms would also help.
> 2. Use a finer η grid, and plot every point in the complex plane coloured by η so we can […].
> 3. Check that the same root is followed all the way along. With projected CAP, that means tracking by overlap, not by energy.
>
> So I know which inputs to change: did you run full CAP-EOM-IP-CCSD in Q-Chem, or projected CAP through pyopencap? I couldn't find Ne–Ar CAP outputs in this folder, so if they're on PACE, tell me the path and I'll look at the trajectory before we change anything.

**User:** full CAP-EOM-IP-CCSD in Q-Chem

> Thanks, that narrows it down. For full CAP-EOM-IP-CCSD on Ne–Ar, the group's notes […] three likely causes. The first two are quick to check in the output files:
>
> 1. Loose Davidson convergence. The default convergence often leaves the imaginary part […]. In the group's runs, tightening it changed widths by 20–135 %. That alone can make points jump around. The fix is EOM_DAVIDSON_CONVERGENCE 7 (or tighter) in $rem.
> 2. A different state at each η. The Ne 2s hole lies high, at about 48 eV, among many [satellites … each η is a] separate Q-Chem job, and the order of roots can change from job to job. So "root 3" at one η may not be the Ne 2s hole at the next. Plotting "root n" from every job gives exactly this kind of scatter. The fix is to pick the root by its character in each output (large weight on the Ne 2s orbital), not by its position in the list. You can also steer Davidson onto it with [the inner-]valence projector EOM_IP_IV_PROJ.
> 3. The basis is too small, as I described before. aug-cc-pVDZ with no ghost functions gives the outgoing electron almost nothing to occupy, so there may be no real U-turn to find. The fix is aug-cc-pVTZ plus a ghost centre at the midpoint with extra diffuse shells.
>
> Also make sure you plot the first-order corrected (deperturbed) energies, not the raw one[s].
>
> Next step: can you give me the path to the outputs (and one input) for this η scan? I'll [run the output che]cker, find which root is the Ne 2s hole in each job, and replot the trajectory with the right root and the corrected energies. That costs no compute. It tells us whether the U-turn is hidden by points from other states (no new jobs needed) or whether we really need tighter convergence and a bigger basis.

---

## Without the plugin

**User:** I am having an issue with some of my CAP results, where I don't see a clean U-turn, instead the values just bounce around in Re vs Im and there is no clear trend.

> Working directory is empty, so I can't see your data yet. Assuming you mean complex absorbing potential trajectories (E(η) plotted as Re vs Im, looking for the cusp or U-turn that marks the resonance), these are the usual causes of scatter, roughly from most to least common:
>
> **1. You're following the wrong root (most likely cause)**
> If you pick "root n" at each η by index or by sorting on Re(E), the label jumps between states wherever they come close in energy. The plot then hops between several real trajectories and looks like noise.
> - **Check:** plot all roots at every η, each η in its own color. If smooth curves appear in the cloud, this is the problem.
> - **Fix:** track by eigenvector overlap. At each step, take the root with the largest |⟨c(ηᵢ)|c(ηᵢ₋₁)⟩|, using the c-product for complex-symmetric H, not the Hermitian inner product. OpenCAP and similar tools have this built in.
>
> **2. The η grid is too coarse or the range is off**
> Near the stationary point E changes fast with η, so big jumps make the trajectory look random.
> - **Fix:** use a log-spaced grid over several decades, e.g. 1e-5 to 1e-1 a.u. with 50–200 points, and refine around where the curve turns.
>
> **3. The basis can't describe a resonance**
> Without enough diffuse functions the continuum isn't discretized well, and there's nothing to stabilize.
> - **Fix:** add extra diffuse shells (e.g. aug-cc-pVTZ+3s3p, or extra diffuse functions on a ghost atom at the center of mass).
> - **Check:** see whether Re(E) of the state moves a lot as you add diffuse functions.
>
> **4. The state isn't actually a resonance**
> - A pseudo-continuum state runs almost straight toward large negative Im(E) with no turn.
> - A bound state barely moves.
>
> So check which kind of state you're actually tracking.
>
> **5. Projected CAP subspace is too small** (OpenCAP / projected CAP-EOM)
> - **Fix:** include more states so the resonance has enough partners to mix with. Results should stop changing as you add states.
>
> **6. CAP box placement**
> - If the onset is too tight, the CAP cuts into the valence density.
> - If it's too loose, the CAP has almost no effect until η is large.
> - The default box is usually based on ⟨r²⟩ of the neutral ground state; try scaling it.
>
> **7. Solver or plotting artifacts**
> - Unconverged EOM/CI roots at individual η values can add random jitter. Check the convergence flags.
> - Make sure the points are sorted by η before you draw lines between them.
>
> **Also worth doing:** compute the first-order corrected trajectory U(η) = E(η) − η·dE/dη. It often shows a much clearer stationary point (a kink or loop) when the raw E(η) looks vague.
>
> If you share the output files or the E(η) data, plus the code (Q-Chem, OpenCAP+PySCF/Molcas, etc.), method, basis and η range, I can write a script that tracks roots by overlap, computes the corrected trajectories and finds the stationary points. That should tell us quickly which of these is the cause.

**User:** I am running with the aug-cc-pVDZ basis for the argon neon dimer

> aug-cc-pVDZ is very likely the main problem, possibly together with root flipping.
>
> I'm assuming you're computing the ICD width of the Ne 2s⁻¹ state in NeAr (Ne⁺(2s⁻¹)Ar → Ne⁺(2p⁻¹)Ar⁺ + e⁻). If you're after something else, such as an electron-attachment resonance, let me know, though the basis issue applies either way.
>
> **Why aug-cc-pVDZ won't give a clean trajectory**
> - **The continuum is barely there.** aug-cc-pVDZ adds only one diffuse shell per angular momentum per atom. The CAP needs a reasonably dense set of discretized continuum states for the resonance to couple to. With only a few, E(η) gets pushed around by a handful of individual pseudo-continuum states, and you see erratic motion instead of a smooth curve with a stationary point.
> - **ICD widths are tiny** (meV scale), so Im(E) at the stationary point is small. Wiggles from the poor continuum and from root mixing can easily be as large as the effect you're trying to see.
> - **The energy region is crowded.** Ne 2s⁻¹ (~48 eV) sits in a region with Ar 3p⁻² nl satellite (2h1p) states. Those can swap places with your state as η changes, which looks like scatter if you track roots by index.
>
> **What to change**
> 1. **Add extra diffuse functions.** Keep aug-cc-pVDZ (or go to aug-cc-pVTZ) on Ne and Ar, and add even-tempered diffuse shells: take the most diffuse aug exponent for each l and keep dividing by ~2 to get 3–5 extra s, p and d shells. These can go on each atom or on a ghost atom at the dimer midpoint or center of mass. CAP studies of ICD typically use basis sets like this.
> 2. **Check the basis is converged.** Add diffuse shells until the stationary-point Re(E) and Γ stop changing noticeably. If Γ still jumps around as you add shells, the continuum isn't converged yet.
> 3. **Track the root by overlap.** At each η, pick the root with the largest overlap (c-product) with the previous step's eigenvector, or with the largest Ne 2s⁻¹ weight. Don't pick by index.
> 4. **Use a fine log-spaced η grid that goes low enough.** Small widths often mean a small optimal η. Something like 1e-6 to 1e-2 a.u. with 100+ points is a reasonable start.
> 5. **Look at the corrected trajectory** U(η) = E − η·dE/dη. It usually shows a clearer stationary point than the raw E(η).
> 6. **Fix the geometry.** ICD widths depend strongly on the Ne–Ar distance, so make sure R is fixed and sensible (near the equilibrium, around 3.5 Å).
>
> If you send your output or the E(η) data, and tell me which code you're using (Q-Chem, OpenCAP, etc.) and which method (EOM-IP-CCSD, ADC, …), I can:
> - write the overlap-based tracking and corrected-trajectory script,
> - generate the even-tempered diffuse exponents for Ne and Ar in your code's basis format.

**User:** full CAP-EOM-IP-CCSD in Q-Chem

> With full CAP-EOM-IP-CCSD in Q-Chem, every η value is a separate job. The Davidson solver starts from scratch each time, so it doesn't automatically land on the same state, and that's very likely where much of your scatter comes from. Combined with aug-cc-pVDZ, it explains what you're seeing.
>
> **1. Lock onto the Ne 2s⁻¹ state explicitly**
> Ne 2s⁻¹ (~48 eV) sits high in the IP spectrum, above many Ne 2p⁻¹, Ar 3p⁻¹, Ar 3s⁻¹ and satellite states. If you request `IP_STATES = [n,...]` and take "the nth root", the root you get can change from one η to the next.
> - **Use symmetry.** NeAr is run in C2v, and Ne 2s is σ, so A1. Request roots only in A1, e.g. `IP_STATES = [6,0,0,0]` (check the irrep order Q-Chem prints).
> - **Better, use a user guess.** Set `EOM_USER_GUESS = TRUE` with an `$eom_user_guess` section that ionizes the Ne 2s orbital. Then Davidson starts from that state at every η, not from the lowest Koopmans guesses.
> - **Check the result every time.** Confirm the dominant R1 amplitude is the Ne 2s orbital. Look at its weight too: if it drops sharply at some η, the state has mixed with an Ar satellite.
> - **Converge tightly.** Tighten `EOM_DAVIDSON_CONVERGENCE`, raise `EOM_DAVIDSON_MAXITER`, and make sure every root actually converged. High-lying roots sometimes stop on a different state.
>
> **2. Fix the basis**
> - Use `BASIS = GEN` (or MIXED). Start from aug-cc-pVDZ (aug-cc-pVTZ if you can afford it) and add 3–4 even-tempered s, p and d shells on both atoms.
> - The new exponents are α_k = α_diffuse / 2^k for k = 1…N, where α_diffuse is the most diffuse aug exponent for each l. Take those from the Basis Set Exchange entry for Ne and Ar.
> - Keep `PURECART` consistent with the parent basis.
> - Run a quick test: add one more set of shells and see whether Re(E) and Γ at the stationary point stop moving.
>
> **3. CAP box**
> - Q-Chem prints ⟨X²⟩, ⟨Y²⟩, ⟨Z²⟩ for the neutral SCF. A common starting choice is onset = √⟨X²⟩ etc., so CAP_Z (the bond axis) should be larger than CAP_X/CAP_Y.
> - Then scale the box by 0.8–1.2 and check that the stationary-point Γ holds up.
> - Units are easy to get wrong. As I remember it, `CAP_ETA` is in 10⁻⁵ a.u. and `CAP_X/Y/Z` are in 10⁻³ bohr, but verify that in the manual for your Q-Chem version. An η grid that is off by a factor of 1000 would also look like nonsense.
>
> **4. η grid and analysis**
> - **Grid:** use 30–60 log-spaced points, e.g. 1e-5 to 1e-2 a.u. You can coarsen the grid once you've found the turning region.
> - **Energies to plot:** use total energies of the ionized state, or IEs. Either works as long as you're consistent; the neutral is bound, so its η dependence is small.
> - **Corrected trajectory:** compute U = E − η·dE/dη by finite differences. Take the width from where |η·dE/dη| (or the corrected version) is smallest: Γ = −2·Im(E).
>
> If you send one or two of your Q-Chem outputs, or just the input and a list of (η, Re E, Im E) values, I can:
> - check root identity and convergence from the amplitudes,
> - write a script that scans the η jobs, extracts the Ne 2s⁻¹ root, and plots raw and corrected trajectories,
> - build the `$basis` section with the extra diffuse shells.
