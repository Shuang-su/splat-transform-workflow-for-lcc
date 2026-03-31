# Workflow Reference

This document records the exact workflow conventions used in this repo.

## Core scripts

- `plugins/splat-transform-for-lcc/scripts/scene_workflow.py`
- `plugins/splat-transform-for-lcc/scripts/merge_settings.py`

## Defaults used by `deploy-scene`

- `rotation = 90,0,0`
  This is the common default rotation for this workflow. It is a starting point, not a guaranteed truth for every LCC scene.
- `voxel source = LOD0`
  Voxel generation only uses the finest main scene LOD layer.
- `R = 0.08`
  Voxel resolution in meters. Lower values create denser and larger collision data.
- `A = 0.20`
  Alpha threshold. Higher values ignore weaker semi-transparent edges.

## Important `splat-transform` CLI rule

Per-file transforms must be written after the input file they belong to.

Correct:

```bash
node splat-transform/bin/cli.mjs input.lcc -r 90,0,0 output/lod-meta.json
```

Incorrect:

```bash
node splat-transform/bin/cli.mjs -r 90,0,0 input.lcc output/lod-meta.json
```

This repo's `splat-transform` copy contains a local guard that errors when the wrong ordering is used.

## Settings workflows

### v1 + base v2 -> merged version 2 settings

```bash
python3 plugins/splat-transform-for-lcc/scripts/merge_settings.py \
  /path/to/settings.json \
  /path/to/settings-merged.json \
  --base-v2 /path/to/settings-v2.json
```

Use this when you want to keep annotations, post effects, tonemapping, and other viewer-side version 2 configuration.

### v1 -> v2 conversion

```bash
python3 plugins/splat-transform-for-lcc/scripts/merge_settings.py \
  /path/to/settings.json \
  /path/to/settings-v2.json
```

Use this when only the simple v1 `settings.json` exists.

## Scene workflow commands

### `merge-settings`

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py merge-settings \
  /path/to/settings.json \
  /path/to/settings-merged.json \
  --base-v2 /path/to/settings-v2.json
```

### `convert-scene`

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py convert-scene \
  /path/to/scene.lcc \
  /path/to/output-root \
  --splat-transform /path/to/splat-transform \
  --rotation 90,0,0 \
  --voxel-lod 0 \
  --voxel-resolution 0.08 \
  --voxel-alpha 0.20
```

### `deploy-scene`

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py deploy-scene \
  my-scene \
  /path/to/render/scene.lcc \
  /path/to/render \
  /path/to/supersplat-viewer/public \
  /path/to/settings.json \
  --base-v2 /path/to/settings-v2.json \
  --splat-transform /path/to/splat-transform \
  --rotation 90,0,0 \
  --voxel-lod 0 \
  --voxel-resolution 0.08 \
  --voxel-alpha 0.20
```

## Included source modifications

### `supersplat-viewer`

This repo preserves the local viewer worktree, including:

- gradient background support in settings schema and runtime
- transparent clear-color handling used by gradient backgrounds
- content transform support
- voxel collider and walk/fly alignment changes

### `splat-transform`

This repo preserves the local transform worktree, including:

- CLI validation for misordered per-file transform arguments
- README guidance for that CLI behavior
