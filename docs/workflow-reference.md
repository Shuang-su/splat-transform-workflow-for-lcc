# Workflow Reference

This document records the exact workflow conventions used in this repo.

## Core scripts

- `plugins/splat-transform-for-lcc/scripts/scene_workflow.py`
- `plugins/splat-transform-for-lcc/scripts/merge_settings.py`

## Defaults used by `deploy-scene`

- `--splat-transform = splat-transform-2.1.1`
  The script prefers the repo-local 2.1.1 tree when `SPLAT_TRANSFORM_DIR` and `--splat-transform` are not set.
- `--stream-rotation auto`
  LCC on 2.x uses no extra `-r`; legacy LCC and PLY use `90,0,0`.
- `--sog-rotation auto`
  PLY uses `90,0,0`; LCC on 2.x uses no extra `-r`.
- `--voxel-rotation auto`
  PLY on 2.x uses `-90,0,180`; legacy inputs use `90,0,0`.
- `voxel size = 0.08`
  Voxel resolution in meters. Lower values create denser and larger collision data.
- `opacity threshold = 0.20`
  Alpha threshold. Higher values ignore weaker semi-transparent edges.

## Versioned `splat-transform` directories

- `splat-transform-1.9.2/`
  Legacy reference used by the original workflow. Use it only when reproducing older 1.9.2 outputs.
- `splat-transform-2.1.1/`
  Current default for new conversions.

The 2.x LCC reader marks LCC data with an internal `90,0,180` source transform. That is why 2.x LCC streamed output should not also receive the old `-r 90,0,0`. PLY is different: PLY remains a PLY-space source, so this workflow still uses `input.ply -r 90,0,0 output/scene.sog` for PLY-derived SOG.

Voxel CLI parameters also differ:

```bash
# 1.9.2
splat-transform -O 0 -R 0.08 -A 0.20 input.lcc -r 90,0,0 output/walk.voxel.json

# 2.1.1 PLY baked voxel
splat-transform --voxel-params 0.08,0.20 input.ply -r -90,0,180 output/walk.voxel.json
```

## Important `splat-transform` CLI rule

Per-file transforms must be written after the input file they belong to.

Correct:

```bash
node splat-transform-2.1.1/bin/cli.mjs input.ply -r 90,0,0 output/scene.sog
```

Incorrect:

```bash
node splat-transform-2.1.1/bin/cli.mjs -r 90,0,0 input.ply output/scene.sog
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
  --sog-input /path/to/point_cloud.ply \
  --voxel-input /path/to/point_cloud.ply \
  --splat-transform /path/to/splat-transform-2.1.1 \
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
  --sog-input /path/to/point_cloud.ply \
  --voxel-input /path/to/point_cloud.ply \
  --splat-transform /path/to/splat-transform-2.1.1 \
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

### `splat-transform-1.9.2`

This repo preserves the legacy transform worktree, including:

- CLI validation for misordered per-file transform arguments
- README guidance for that CLI behavior

### `splat-transform-2.1.1`

This repo also includes the current 2.x transform worktree used by new PLY-first SOG and voxel conversions.
