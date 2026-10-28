---
name: blender-molecular-rendering
description: Set up and use Blender with Claude (live MCP connection or headless bpy scripts) to render publication-quality molecular / cluster figures (atoms, bonds, density clouds) with matplotlib overlays. Use when asked to make 3D renders of molecules, clusters or surfaces, or when connecting Claude to a running Blender.
---

# Blender for molecular figures (Kretchmer group notes)

Two ways to drive Blender. **Headless is the reliable default**; the live connection is nice for interactive tweaking and for letting Claude look at the scene itself. If live is not connected, say so and fall back to headless; do not burn time debugging it mid-task.

## 1. Live connection, macOS

### Root cause of our multi-hour failure (Oct 2026): wrong add-on
The community add-on `ahujasid/blender-mcp` (GitHub `addon.py` + `uvx blender-mcp` in `claude_desktop_config.json`) failed silently: calls connected but hung forever. **Switching to the official Blender Lab MCP connector fixed it instantly**; the first `get_objects_summary` call worked. Use the official one and nothing else.

### Correct install (official Blender Lab connector)
1. **Blender 5.1+** (we use 5.2 LTS, `/Applications/Blender.app`).
2. **Remove the community add-on completely first.** Both listen on port 9876 and conflict. Uninstall it in Preferences > Add-ons, and delete any leftover copy under Blender's `scripts/addons`. Also remove any `blender-mcp` / `uvx` entry from `claude_desktop_config.json`.
3. **Claude Desktop:** Customize > Connectors > search "Blender" > add it. A plain "Blender — Desktop" entry may already be listed. This installs the Blender Lab server (`blender-mcp` package, module `blmcp`, run with `uv`; source `https://projects.blender.org/lab/blender_mcp`). No `mcpServers` entry is needed in `claude_desktop_config.json`.
4. **Blender add-on:** on blender.org's MCP server page, drag the "Drag and Drop into Blender" box onto the open Blender window **twice**. The first drag adds the lab extension repository (accept the dialog). The second drag installs the add-on. The repository is `https://lab.blender.org/`; it can also be added by hand under Preferences > Get Extensions > Repositories.
5. **Edit > Preferences > Add-ons:** find "MCP" (v1.0.3, two-person icon), enable it, expand it, and confirm "Server is running" on `localhost:9876`. It also has its own settings (Timer Interval, Idle Delay, Auto Start).
6. If the server will not start and reports `Online access must be enabled in the system preferences`, enable Preferences > System > Allow Online Access (or pass `--online-mode` to command-line Blender). This message is in the add-on code. It was not our problem, but it is a possible blocker.
7. **Claude Code** does NOT inherit Desktop connectors. Give it an MCP config file:
   ```json
   {"mcpServers":{"blender":{"command":"uv","args":["run","--directory","<extension folder containing pyproject.toml>","blender-mcp"]}}}
   ```
   and start `claude --mcp-config blender_mcp.json`. `uv` must be on PATH (`~/.local/bin`). Env overrides: `BLENDER_MCP_HOST`, `BLENDER_MCP_PORT`.

### Verify
- `lsof -nP -iTCP:9876 -sTCP:LISTEN`: only Blender should be listening. Zotero uses 19876; don't misread it.
- Call a read-only tool (`get_objects_summary`). A Desktop chat can have the connector enabled but no Blender tools; start a new chat after enabling.

### Diagnosing a hang (how we found the root cause)
- **Start Blender from a terminal** (`/Applications/Blender.app/Contents/MacOS/Blender`) to see its console. A healthy call shows `Connected to client` > `Client handler started` > `Queued command: ...`. Our broken case showed `Connected to client` > `Client handler started` > `Client disconnected` with **no `Queued command:` line**: the client connected but never sent a parseable command.
- **Read `~/Library/Logs/Claude/mcp-server-Blender.log`.** If `initialize`, `tools/list`, `prompts/list` and `resources/list` appear but there is **no `method="tools/call"` line** for the hanging call, the request never reached the server. That means a client/connector problem, not Blender.
- An instant `cannot connect to localhost:9876` means Blender, the add-on, or its server is not running. A *hang* after connecting means the wrong or broken add-on/server pair.

### False leads (none of these fixed it; skip them)
- macOS App Nap (`defaults write`, `caffeinate`).
- Stale port/socket (`lsof -ti :9876 | xargs kill -9`). Worth doing as cleanup, but not the fix.
- IPv6 / firewall.
- Claude Desktop's "Use built-in Node.js for MCP" toggle (suggested online; unverified).
- Patching `bl_info` `blender` from (4,0,0) to (5,0,0). That field is a minimum version, not a maximum.
- Restarting Claude Desktop (Cmd-Q) or re-approving permissions.
- Community add-on naming: its sidebar tab is "MCP for Blender" (N-panel > Connect to Claude), installed via Add-ons > dropdown > Install from Disk. Irrelevant once you use the official connector.

### Fallbacks while live is down
- The `*_for_cli` Blender MCP tools work headless on a saved `.blend` file, with no socket and no add-on. Save the scene (File > Save As) to make this possible.
- Plain headless `bpy` scripts (section 2).
- A simple file-watcher bridge script (Blender polls a folder for scripts to run) worked as a stopgap.

### Once live works
- **Look at the scene yourself** with `get_screenshot_of_window_as_image` instead of asking the user for screenshots. That is how we caught the next two bugs.
- **Viewport shading on SOLID ignores material colours.** Switch to Material Preview or Rendered before judging colours.
- **Camera framing:** fit the view with `tan(fov/2)`, not `sin`; using sin made every render too small. With an orthographic camera, set `ortho_scale` from the object extent.
- Other gotcha: a relaunched Claude Code session started from inside another session loses its transcript unless the inherited `CLAUDE*` / `ANTHROPIC*` env vars are stripped first.

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
- **Schematics are the exception, when the user asks:** sizes may be exaggerated for readability (e.g. enlarge the water, or draw Ar and O the same size). Keep the chosen scale the same across the schematic set, and keep it separate from the true-scale figures. If small markers (e.g. trajectory "cloud" dots) were sized relative to an atom, rescale them too.
- Lighting: white world at strength ~0.3 plus one sun (energy ~1.7, angle ~12°). Camera: orthographic, placed from a centre point, elevation angle and `ortho_scale`; keep the same camera across versions when asked.
- Density clouds (e.g. hole densities): Gaussian sum on a grid -> Principled Volume with a smooth MapRange cutoff, `volume_step_rate` ~0.25, LOW emission (bright clouds look like they are glowing). Make the volume camera-ray-only (disable diffuse/glossy/transmission/scatter/shadow visibility) so it does not tint neighbouring atoms. Render clouds as separate layers and composite so foreground atoms stay opaque.

Labels and annotation: never in Blender. Export each atom's pixel position with `bpy_extras.object_utils.world_to_camera_view` to a JSON next to the PNG, then draw all labels, arrows and legends in matplotlib on top of the render (vector text, consistent fonts; see the `scientific-plot-style` skill).

## 3. VMD instead of Blender

For quick structure images rendered on the cluster with VMD and Tachyon (headless, `vmd -dispdev text`), read `references/vmd.md` first: several commands fail silently there.

## 4. Workflow rules
- Render ONE image and get approval before batch-rendering the rest.
- Save new versions (`_v2`, `_v3`, ...); never overwrite an approved render.
- Matplotlib side needs a Python with numpy/matplotlib (Blender's bundled Python is separate).
- No installs (Blender, add-ons, uv packages) without the user's OK.
