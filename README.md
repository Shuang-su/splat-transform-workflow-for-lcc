# splat-transform-for-lcc

This mono-repo packages the LCC-to-SuperSplat workflow we built in Codex so it can be cloned and reused on another machine.

It includes:

- a modified `supersplat-viewer` source tree
- versioned `splat-transform` source trees for legacy 1.9.2 and current 2.1.1 workflows
- a repo-local Codex plugin and skill
- helper scripts for scene conversion, settings merge, and viewer mounting
- two ready-to-open demos: `baoan` and `dashi`

## Repo layout

```text
splat-transform-for-lcc/
├── .agents/plugins/marketplace.json
├── docs/
│   ├── thread-summary.md
│   ├── splat-transform-versions.md
│   ├── upstream-lock.json
│   └── workflow-reference.md
├── install_skill.sh
├── plugins/
│   └── splat-transform-for-lcc/
│       ├── .app.json
│       ├── .codex-plugin/plugin.json
│       ├── scripts/
│       │   ├── merge_settings.py
│       │   └── scene_workflow.py
│       └── skills/
│           └── supersplat-workflow/
├── splat-transform-1.9.2/
├── splat-transform-2.1.1/
└── supersplat-viewer/
```

## splat-transform versions

This repo keeps both transform sources intentionally:

- `splat-transform-1.9.2/` is the legacy reference used by the original workflow.
- `splat-transform-2.1.1/` is the default for new conversions and is preferred by `scene_workflow.py` when `--splat-transform` is omitted.

The important workflow difference is that `splat-transform` 2.x reads LCC with an internal `90,0,180` source transform. Do not add the old LCC `-r 90,0,0` on top of 2.x LCC streamed output. PLY does not use that LCC-specific correction, so PLY-derived SOG still uses `input.ply -r 90,0,0 output/scene.sog`.

More detail is recorded in [docs/splat-transform-versions.md](docs/splat-transform-versions.md).

## What the default workflow does

The end-to-end command is:

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py deploy-scene ...
```

By default it:

- converts an `.lcc` scene into streamed LOD output
- generates `scene.sog` from original PLY when `--sog-input` is provided
- generates voxel collision data from original PLY when `--voxel-input` is provided
- merges settings into a version 2 viewer JSON
- mounts the result into a local `supersplat-viewer/public/<scene>` route

## Parameter meanings

The default deploy parameters are intentionally opinionated and must be understood on first use:

- `--stream-rotation auto`
  LCC on 2.x uses no extra `-r`; legacy LCC and PLY use `90,0,0`.
- `--sog-rotation auto`
  PLY uses `90,0,0`; LCC on 2.x uses no extra `-r`.
- `--voxel-rotation auto`
  PLY on 2.x uses `-90,0,180`; legacy inputs use `90,0,0`.
- `--voxel-lod 0`
  Selects the legacy LCC voxel source level when voxel input is LCC.
- `--voxel-resolution 0.08`
  Voxel size in meters. Smaller values are more precise but produce larger files and heavier collision data.
- `--voxel-alpha 0.20`
  Alpha threshold for voxelization. Higher values ignore more weak or semi-transparent edges.

Also remember this `splat-transform` rule:

- `-r` and `-t` must be written after the input file they apply to.
- Correct example:

```bash
node splat-transform-2.1.1/bin/cli.mjs input.ply -r 90,0,0 output/scene.sog
```

If you put `-r` or `-t` before the input file, the transform will not apply to that file.

## Settings workflow

This repo supports two settings flows.

### 1. v1 + base v2 -> merged version 2 settings

Use:

```bash
python3 plugins/splat-transform-for-lcc/scripts/merge_settings.py \
  /path/to/settings.json \
  /path/to/settings-merged.json \
  --base-v2 /path/to/settings-v2.json
```

Use this when you want to keep version 2 annotations, post effects, tonemapping, and related viewer config.

### 2. v1 -> v2 conversion

Use:

```bash
python3 plugins/splat-transform-for-lcc/scripts/merge_settings.py \
  /path/to/settings.json \
  /path/to/settings-v2.json
```

Use this when you only have the simple v1 `settings.json`.

## Common commands

### Merge settings

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py merge-settings \
  /path/to/settings.json \
  /path/to/settings-merged.json \
  --base-v2 /path/to/settings-v2.json
```

### Convert scene only

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py convert-scene \
  /path/to/scene.lcc \
  /path/to/output-root \
  --sog-input /path/to/point_cloud.ply \
  --voxel-input /path/to/point_cloud.ply \
  --splat-transform /path/to/splat-transform-2.1.1 \
  --voxel-resolution 0.08 \
  --voxel-alpha 0.20
```

### Full deploy

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

## Install on another machine

1. Clone this repo.
2. Open the repo as a Codex workspace so the repo-local plugin marketplace is visible.
3. Optionally install the skill globally:

```bash
./install_skill.sh
```

That creates a symlink at `~/.codex/skills/supersplat-workflow`.

4. Make sure the machine has:
   - `python3`
   - `node`
   - local dependencies installed for the copied `supersplat-viewer` and whichever `splat-transform-*` version you run

## Included demos

- `supersplat-viewer/public/baoan/`
- `supersplat-viewer/public/dashi/`

These are kept as cross-machine smoke tests and reference routes.

## Notes

- `supersplat-viewer` in this repo already contains the local gradient-background support and related viewer changes.
- `splat-transform-1.9.2` preserves the legacy CLI guard that errors when per-file transform arguments are placed before the input file.
- `splat-transform-2.1.1` is the current default used by the workflow scripts.
- More detail is recorded in [docs/workflow-reference.md](docs/workflow-reference.md) and [docs/thread-summary.md](docs/thread-summary.md).
