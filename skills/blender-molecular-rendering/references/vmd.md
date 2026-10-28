# Headless VMD + Tachyon on a cluster: gotchas

Lessons from rendering cluster images with VMD 1.9.4a57 on PACE (`vmd -dispdev text`, no display), Sep 2026. All of these fail **silently**: no Tcl error, and `catch {}` catches nothing. A run that looks "just slow" may be stuck or may have skipped the render.

## Running the script
- **Don't pass a long script with `vmd -e script.tcl`.** It stopped partway through complex scripts. Use a tiny driver that does `source script.tcl` (then `quit`).
- **Delete `display background white`.** Under `-dispdev text` it made `source` return early, so nothing after it ran (including the `render` line) and no image was written. Set the background with `color Display Background white` instead; that is the one that affects the render. (This may also have been the real cause of the `-e` truncation above.)
- **Debug with flushed checkpoints.** VMD's output is block-buffered when stdout is not a terminal, so logs look cut off. Put `puts "step N"; flush stdout` after each line to find where it stops.

## Rendering
- **Use the external Tachyon binary, not `render TachyonInternal`.** TachyonInternal needs an OpenGL context; on at least one compute node it wrote a completely white image while printing a normal "Rendering complete" log. This form worked on every node tried:
  ```tcl
  render Tachyon out.dat "<path>/tachyon_LINUXAMD64" -aasamples 12 %s -format TARGA -res W H -o out.tga
  ```
- **Check the image** (convert TGA to PNG and look at it, or count non-white pixels) before rendering a batch.

## Slurm
- **Request all cores of the node** (e.g. `srun -c 24` on a 24-core node; check with `sinfo -p <partition> -o "%P %c"`). VMD sizes its thread pool from the node's full core count; with a smaller `-c` the `sched_setaffinity` calls fail (`wkf_thread_set_self_cpuaffinitylist: sched_setaffinity: Invalid argument`) and VMD hangs at ~0 % CPU right after the "Fragments: N" line.
- **Keep scripts, logs and outputs on shared storage.** `/tmp` is node-local, so a driver in `/tmp` on the login node is not visible to the `srun` job.

## Matching sphere sizes
- `VDW <scale>` uses the real (Bondi) radius times the scale; `CPK <scale>` does not use the same radius table linearly. In one calibration `CPK 2.6 0.4 30 30` drew O the same pixel size as `VDW 0.526 30` drew Ar. If you change representation or scale, re-measure with a two-atom test scene instead of assuming a ratio.
- Exaggerated sizes for schematics follow the same rule as in Blender (`SKILL.md` §2): only when asked, and consistent across the set.

Labels, arrows and legends go on in matplotlib afterwards, as for Blender renders (`scientific-plot-style`).
