---
name: supersplat-workflow
description: Use when converting XGRIDS or 其域 `.lcc` scenes into SuperSplat streamed LOD and voxel outputs, generating high-precision SOG or voxel outputs from original PLY, merging v1 and v2 settings JSON files, mounting scenes into a local `supersplat-viewer` route, or packaging the workflow for reuse on another machine.
---

# SuperSplat Workflow

Use the bundled scripts instead of retyping the workflow by hand. Prefer original PLY as the high-precision source for SOG and voxel outputs when it is available.

## What this skill is for

- Convert `.lcc` into true streamed LOD output for SuperSplat
- Generate high-precision `scene.sog` from PLY when original PLY is available
- Generate `walk.voxel.json` and `walk.voxel.bin` from PLY when original PLY is available
- Keep or remove the environment layer
- Merge a simple `settings.json` with a version 2 settings JSON
- Mount streamed LOD and voxel files into `supersplat-viewer/public/<scene>`

## Coordinate-space rules

- PLY, SOG, SPZ, KSplat, and splat inputs are PLY-space sources.
- In `splat-transform` 2.x, LCC is read with an internal source transform of `90,0,180`; do not blindly add the old LCC `90,0,0` rotation on top of it.
- `meta.json.version: 2` is the SOG/LOD data format version, not the `splat-transform` CLI version.
- If old `PLY -> SOG` conversion needed `-r 90,0,0` for viewer alignment, keep using that for PLY. The LCC 2.x internal transform does not apply to PLY.

## Important CLI rule

When calling `splat-transform` directly, per-file transforms must come after the input file:

```bash
splat-transform input.ply -r 90,0,0 -t 0,0,0 output.sog
```

Do not put `-r` or `-t` before the input file.

## Preferred scripts

### End-to-end scene deployment

Use:

```bash
python3 ../../scripts/scene_workflow.py deploy-scene ...
```

This will:

1. Merge settings into a version 2 JSON
2. Convert the stream input into streamed LOD
3. Generate `scene.sog`
4. Generate voxel output
5. Mount streamed LOD and voxel files into a local `supersplat-viewer/public/<scene>` route

When original PLY exists, pass it as both SOG and voxel input:

```bash
python3 ../../scripts/scene_workflow.py deploy-scene \
  scene-key \
  /path/to/meta.lcc \
  /path/to/output \
  /path/to/supersplat-viewer/public \
  /path/to/settings.json \
  --sog-input /path/to/point_cloud.ply \
  --voxel-input /path/to/point_cloud.ply
```

The positional input remains the streamed LOD source. Use LCC there for true multi-LOD streamed output. Use PLY there only when single-layer streamed output is acceptable, or when the PLY already has a `lod` column.

### Standalone conversion

Use:

```bash
python3 ../../scripts/scene_workflow.py convert-scene \
  /path/to/meta.lcc \
  /path/to/output \
  --sog-input /path/to/point_cloud.ply \
  --voxel-input /path/to/point_cloud.ply
```

The script prints the generated streamed LOD, SOG, and voxel paths.

### Standalone settings merge

Use:

```bash
python3 ../../scripts/merge_settings.py v1.json output.json --base-v2 base-v2.json
```

Use the base v2 file when you need to preserve annotations, post effects, tonemapping, and other viewer configuration.

## Direct `splat-transform` examples

For `splat-transform` 2.x with original PLY:

```bash
splat-transform input.ply -r 90,0,0 output/scene.sog
splat-transform --voxel-params 0.08,0.20 input.ply -r -90,0,180 output/walk.voxel.json
```

For `splat-transform` 2.x with LCC streamed LOD:

```bash
splat-transform input.lcc output/lod-meta.json
```

For legacy 1.9.2 LCC:

```bash
splat-transform input.lcc -r 90,0,0 output/lod-meta.json
splat-transform -O 0 -R 0.08 -A 0.20 input.lcc -r 90,0,0 output/walk.voxel.json
```

## Workflow defaults

- `--splat-transform`: repo-local `splat-transform-2.1.1/` when available, unless `SPLAT_TRANSFORM_DIR` or an explicit flag overrides it
- Streamed source: LCC for true multi-LOD streamed output
- SOG source: original PLY when available
- Voxel source: original PLY when available
- `--stream-rotation auto`: LCC on 2.x uses no extra `-r`; legacy LCC and PLY use `90,0,0`
- `--sog-rotation auto`: PLY uses `90,0,0`; LCC on 2.x uses no extra `-r`
- `--voxel-rotation auto`: PLY on 2.x uses `-90,0,180`; legacy inputs use `90,0,0`
- Voxel defaults: size `0.08`, opacity threshold `0.20`
- Mounted voxel names: `walk.voxel.json` and `walk.voxel.bin`
- Mounted LOD directory name: `streamed`

## First-use parameter meanings

- `--sog-input`
  High-precision source for `scene.sog`; use original PLY when available.
- `--voxel-input`
  High-precision source for `walk.voxel.json`; use original PLY when available.
- `--splat-transform`
  Use `splat-transform-2.1.1/` for new conversions. Use `splat-transform-1.9.2/` only when reproducing legacy results.
- positional stream input
  Source for streamed LOD. Use LCC for true multi-LOD. PLY streamed output is single-layer unless the PLY already has LOD labels.
- `--stream-ply-lod = 0`
  When streamed input is PLY, the script tags it with `-l 0` by default so `lod-meta.json` can be written.
- `LOD0`
  Legacy LCC voxel source level.
- `voxel size = 0.08`
  Voxel size in meters. Smaller values are more detailed but produce larger collision files.
- `opacity threshold = 0.20`
  Alpha threshold for voxelization. Higher values ignore more weak or semi-transparent edges.

## Settings workflows

Two settings workflows are supported:

- `v1 + base v2 -> merged version 2 settings`
- `v1 -> version 2 settings`

Use:

```bash
python3 ../../scripts/merge_settings.py settings.json settings-merged.json --base-v2 settings-v2.json
```

or:

```bash
python3 ../../scripts/merge_settings.py settings.json settings-v2.json
```

## When to remove environment

Add `--remove-environment` only when the user explicitly wants the environment stripped.
Otherwise keep the generated `env/` directory and `environment` entry in `lod-meta.json`.

## Generated viewer route

The mount step creates:

- `public/<scene>/settings-merged.json` or the original settings filename
- `public/<scene>/streamed/`
- `public/<scene>/voxel/walk.voxel.json`
- `public/<scene>/voxel/walk.voxel.bin`
- `public/<scene>/index.html`

The route redirects to the root viewer with `settings`, `content`, and `voxel` query params. Do not append a `voxelRotation` query param when using baked PLY voxel output.
