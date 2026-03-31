---
name: supersplat-workflow
description: Use when converting XGRIDS or 其域 `.lcc` scenes into SuperSplat streamed LOD and voxel outputs, merging v1 and v2 settings JSON files, mounting scenes into a local `supersplat-viewer` route, or packaging the workflow for reuse on another machine.
---

# SuperSplat Workflow

Use the bundled scripts instead of retyping the workflow by hand.

## What this skill is for

- Convert `.lcc` into streamed LOD output for SuperSplat
- Generate `LOD0` voxel collision data
- Keep or remove the environment layer
- Merge a simple `settings.json` with a version 2 settings JSON
- Mount the scene into `supersplat-viewer/public/<scene>`

## Important rule

When calling `splat-transform` directly, per-file transforms must come after the input file:

```bash
splat-transform input.lcc -r 90,0,0 -t 0,0,0 output/lod-meta.json
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
2. Convert the `.lcc` scene into streamed LOD
3. Generate voxel output from `LOD0`
4. Mount everything into a local `supersplat-viewer/public/<scene>` route

### Standalone settings merge

Use:

```bash
python3 ../../scripts/merge_settings.py v1.json output.json --base-v2 base-v2.json
```

Use the base v2 file when you need to preserve annotations, post effects, tonemapping, and other viewer configuration.

## Workflow defaults

- Scene rotation default: `90,0,0`
- Voxel source: `LOD0`
- Voxel defaults: `R=0.08`, `A=0.20`
- Mounted voxel names: `walk.voxel.json` and `walk.voxel.bin`
- Mounted LOD directory name: `streamed`

## First-use parameter meanings

- `rotation = 90,0,0`
  This is the common default rotation in this workflow, not a universal truth for all scenes.
- `LOD0`
  Voxels are generated from the finest main scene layer.
- `R = 0.08`
  Voxel size in meters. Smaller values are more detailed but produce larger collision files.
- `A = 0.20`
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

The route redirects to the root viewer with `settings`, `content`, and `voxel` query params.
