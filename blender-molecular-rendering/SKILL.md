---
name: blender-molecular-rendering
description: Set up and use Blender with Claude (live MCP connection or headless bpy scripts) to render publication-quality molecular / cluster figures (atoms, bonds, density clouds) with matplotlib overlays. Use when asked to make 3D renders of molecules, clusters or surfaces, or when connecting Claude to a running Blender.
---

# Blender for molecular figures (Kretchmer group notes)

Two ways to drive Blender. **Headless is the reliable default**; the live connection is nice for interactive tweaking but took hours to get working the first time. If live is not connected, say so and fall back to headless; do not burn time debugging it mid-task.

## 1. Live connection (Blender Lab MCP), macOS

What finally worked (Blender 5.x):
1. **Blender** 5.1+ (we use 5.2 LTS) in `/Applications/Blender.app`.
2. **Blender add-on "MCP"** (Blender Lab, v1.0.3+): Blender > Preferences > Get Extensions > Repositories > add `https://lab.blender.org/`, then install and enable **MCP**. Lands in `~/Library/Application Support/Blender/<ver>/extensions/lab_blender_org/mcp/`.
3. **Preferences > System > Allow Online Access must be ON.** The bridge refuses to start offline ("Online access must be enabled in the system preferences") even though it only listens on localhost. For command-line Blender pass `--online-mode`. This is the most likely hidden blocker.
4. In the add-on prefs: Host `localhost`, Port `9876`, turn on **Auto Start** (or start the server by hand each session). Blender must stay open with the GUI running.
5. **MCP server side.** This is the *Blender Lab* server (`https://projects.blender.org/lab/blender_mcp`, package `blender-mcp`, module `blmcp`, Python >= 3.10, run with `uv`). It is NOT the community `ahujasid/blender-mcp`; do not mix the two (different add-on, different protocol).
   - Claude Desktop: install the "Blender" desktop extension (Blender Lab). It runs `uv run blender-mcp` from its own folder under `~/Library/Application Support/Claude/Claude Extensions/`. No `mcpServers` entry is needed in `claude_desktop_config.json`.
   - Claude Code does NOT inherit Desktop connectors. Give it an MCP config file:
     ```json
     {"mcpServers":{"blender":{"command":"uv","args":["run","--directory","<path to the extension folder containing pyproject.toml>","blender-mcp"]}}}
     ```
     and start `claude --mcp-config blender_mcp.json`. `uv`/`uvx` must be on PATH (`~/.local/bin`).
   - Env overrides: `BLENDER_MCP_HOST`, `BLENDER_MCP_PORT`.
6. **Verify, in this order:**
   - `lsof -nP -iTCP:9876 -sTCP:LISTEN` shows Blender listening. (Other apps use nearby ports, e.g. Zotero on 19876; don't misread it.)
   - In Claude, call a read-only tool such as `get_objects_summary`. A Desktop session can have the connector enabled yet no Blender tools in that particular chat: start a new chat/session after enabling.

Error -> fix:
| Message | Fix |
|---|---|
| `Cannot connect to Blender at localhost:9876 ...` | Blender not open, add-on disabled, or server not started: open Blender, enable MCP, start server / Auto Start |
| `Online access must be enabled in the system preferences` | Preferences > System > Allow Online Access (or `--online-mode`) |
| Tools missing in Claude | new session after enabling; Claude Code needs its own `--mcp-config` |
| Relaunched Claude Code loses transcripts | strip inherited `CLAUDE*` / `ANTHROPIC*` env vars before relaunching from inside another session |

## 2. Headless rendering (default)

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b -P scene.py -- spec.json
```
- Read your own args after `--` (`sys.argv[sys.argv.index('--')+1:]`). Drive it from Python with `subprocess`; cache renders keyed on a hash of (spec + script) so reruns are free.
- Start clean: `bpy.ops.wm.read_factory_settings(use_empty=True)`.
- Engine: Cycles CPU; ~64 samples for drafts, ~160 for finals; wrap OpenImageDenoise in try/except. `film_transparent = True`, RGBA PNG, view transform `Standard` (not Filmic/AgX, which washes out colours).
- Units: 1 Blender unit = 1 Å.

Molecules:
- Atoms: UV spheres (48 × 24), `shade_smooth`, one Principled BSDF per element (roughness ~0.5, specular ~0.2). Bonds: cylinders aligned with `direction.to_track_quat('Z','Y')`.
- Keep element sizes consistent across a figure set. Do not shrink/enlarge special atoms (hole, ion) unless asked; mark them with colour or a label instead.
- Lighting: white world at strength ~0.3 plus one sun (energy ~1.7, angle ~12°). Camera: orthographic, placed from a centre point, elevation angle and `ortho_scale`; keep the same camera across versions when asked.
- Density clouds (e.g. hole densities): Gaussian sum on a grid -> Principled Volume with a smooth MapRange cutoff, `volume_step_rate` ~0.25, LOW emission (bright clouds look like they are glowing). Make the volume camera-ray-only (disable diffuse/glossy/transmission/scatter/shadow visibility) so it does not tint neighbouring atoms. Render clouds as separate layers and composite so foreground atoms stay opaque.

Labels and annotation: never in Blender. Export each atom's pixel position with `bpy_extras.object_utils.world_to_camera_view` to a JSON next to the PNG, then draw all labels, arrows and legends in matplotlib on top of the render (vector text, consistent fonts; see the `scientific-plot-style` skill).

## 3. Workflow rules
- Render ONE image and get approval before batch-rendering the rest.
- Save new versions (`_v2`, `_v3`, ...); never overwrite an approved render.
- Matplotlib side needs a Python with numpy/matplotlib (Blender's bundled Python is separate).
- No installs (Blender, add-ons, uv packages) without the user's OK.
