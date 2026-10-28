---
name: scientific-plot-style
description: House style for scientific figures (matplotlib) - fonts, colour-blind-safe palette, ticks, legends, labels, number formats, delivery - plus the corrections our group keeps giving. Use whenever making or revising a plot, figure panel, spectrum, map or figure overlay for a paper, talk or report.
---

# Scientific plot style (Kretchmer group)

## Start every figure script with the style file
```python
import pubstyle            # pubstyle.py in this skill folder; copy it next to your scripts
pubstyle.apply()
fig, ax = plt.subplots(figsize=(3.4, 2.6))   # single column; ~7.0 in wide for double column
...
pubstyle.panel_tag(ax, '(a)')
pubstyle.save(fig, 'F3_spectrum_v1', outdir)  # always writes PDF + PNG
```
What `apply()` sets:
- **Fonts:** serif (DejaVu Serif, mathtext dejavuserif). Sizes: base 11, axis labels and titles 12, ticks 10, legend 9.5.
- **Ticks:** inward on all four sides, minor ticks on.
- **Lines:** axes 0.9, data lines 1.7.
- **Legend:** no frame.
- **Output:** dpi 150 on screen, 300 saved, `bbox='tight'`.

### Poster and talk variant
The serif, base-11 setting above is the **paper default**; keep it for papers. For posters (and talks, if asked) switch to sans-serif and much bigger text. Apply this after `pubstyle.apply()`:
```python
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Nimbus Sans', 'TeX Gyre Heros', 'Helvetica', 'Arial', 'DejaVu Sans'],
    'mathtext.fontset': 'stixsans',
    'font.size': 20, 'axes.labelsize': 20,
    'xtick.labelsize': 18, 'ytick.labelsize': 18, 'legend.fontsize': 18,
})
```
- Nimbus Sans is the font LaTeX's `\usepackage{helvet}` uses, so it matches a Helvetica poster. Check it resolves (`matplotlib.font_manager.findfont('Nimbus Sans')`) rather than silently falling back to DejaVu.
- Use the figure sizes the author gives for the poster layout; don't shrink the text to fit.

## Colour
- Default palette is Okabe-Ito / Wong, which is colour-blind safe: `pubstyle.C` and `pubstyle.CYCLE`.

  | Name | Hex |
  |---|---|
  | blue | #0072B2 |
  | orange | #D55E00 |
  | green | #009E73 |
  | pink | #CC79A7 |
  | sky | #56B4E9 |
  | yellow | #E69F00 |
  | grey | #666666 |

- Once a palette for a category is approved (e.g. open / marginal / closed = #2166ac / #e6a700 / #b2182b, no data #c8c8c8), never change it across the figure set.
- Categories that must be told apart need clearly different hues. "Too similar" (e.g. teal vs blue) is a common complaint; check side by side.
- The legend swatch must match what is actually drawn, e.g. the lit colour in a 3D render, not the base material colour.
- Avoid red/green-only distinctions. Use hatching or marker shape as a second cue.

## Labels and text
- **Label the level of theory on every number:** e.g. EOM-CC, CCSD(T), DIM, DFT, EXPT, ESTIMATE, PRELIMINARY. Never mix two theories on one axis without saying so.
- **Filenames** carry status: `_PRELIM`, `_DRAFT`, `_PLACEHOLDER`.
- **Units** in axis labels: `Energy (eV)`, `Width (meV)`, `Time (fs)`.
- **Write words out** in labels and legends: "kinetic energy", not "KE". Keep abbreviations for well-known method names (EOM-CC, DFT).
- **Numbers** come from data files, never typed in by hand.
- **Big, readable text:** when in doubt, make labels and legends larger. Keep labels close to what they mark. When the plot is crowded, put the legend outside on the right.
- **No sideways text,** except a vertical colourbar (give it a horizontal title).
- **No captions, footnotes or explanatory prose inside the figure** (no grey "Colour = ..." notes). The author writes all text.
- **Titles:** bold, the same size as the panel tags, and not overclaiming the physics. Paired panels are A1/A2, B1/B2, and so on.
- **Fewer labels, less clutter:** one label per class (e.g. forbidden / borderline / allowed), no values inside legends, and no legend entries for obvious things (O, H, neutral atoms).
- **Remove any line or element that "doesn't tell us anything".**

## Number formats (defaults; follow the paper if it differs)
- Energies / kinetic energies: 2 decimals in eV. Don't show uncertainties unless asked.
- Widths: 3 decimals in meV, with the lifetime (fs or ps) underneath when relevant.
- When asked to restore original tick values or a previous camera or axis range, restore them exactly.

## Common plot types
- **Spectra:** sticks (oscillator strength vs E) plus a Gaussian-broadened curve. State the FWHM. Draw experimental lines or IPs as thin vertical lines. Baseline-shift experimental curves to zero when only their shape matters.
- **Bar comparisons of methods:** reference in black first (e.g. CAP), then the total of the approximate method in grey, then coloured partials, with hatching to separate channels.
- **Hatching to mean "provisional"** is for single values that are not converged, with a legend entry saying so. Don't hatch every bar, and remove the hatch once the value is pinned down (e.g. converged across many jobs or boxes); show its spread as an error band instead.
- **CAP η trajectories:** mark the η where Γ is read (η_opt) with a star on the trajectory. Quote ξ (or any quality metric) at that η_opt, not a median over the whole η range.
- **Maps / scatter:** fixed categorical colours, equal aspect for spatial maps, and distance circles or reference markers instead of text where possible.
- **3D renders:** render in Blender (see `blender-molecular-rendering`), then put every label, arrow and legend on in matplotlib, using exported atom pixel positions.

## Avoid the "AI-generated" look
- No default matplotlib styling.
- No rainbow/jet colour maps. Use viridis/cividis for sequential data, and RdBu for diverging data centred on zero.
- No drop shadows, no gratuitous grids, no 3D bar charts.
- Rebuild a figure in pubstyle rather than patching a cluttered one.

## Delivery
- Write PNG + PDF into the project folder with a versioned name (`_v1`, `_v2`, ...). Never overwrite an approved version.
- Deliver individual panels. The author assembles slides and multi-panel layouts unless asked.
- Show the first figure for approval before producing a whole set.
