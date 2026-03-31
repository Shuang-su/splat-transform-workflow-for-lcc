# Thread Summary

- Thread id: `019d08e5-cf6a-7940-9625-c02b110f4687`
- Thread title: `部署https://github.com/playcanvas/splat-transform的最新版本`
- Time range: `2026-03-20` to `2026-03-31`

## What this thread accomplished

This Codex thread built and refined a repeatable workflow for working with XGRIDS or 其域 `.lcc` scenes:

- local deployment of `splat-transform`
- large-scene streamed LOD generation
- `LOD0` voxel collision generation
- repeated viewer-side validation in `supersplat-viewer`
- local route mounting for many scenes
- settings merge and v1-to-v2 conversion
- packaging results for delivery folders and reuse

## Key decisions captured from the thread

- `rotation = 90,0,0` became the common workflow default for new scene conversion examples, but it is treated as a default, not a universal truth.
- default voxel generation examples use:
  - `LOD0`
  - `R = 0.08`
  - `A = 0.20`
- settings processing supports two flows:
  - `v1 + base v2 -> merged version 2 settings`
  - `v1 -> v2`
- the repo keeps two demo scenes for smoke testing:
  - `baoan`
  - `dashi`

## Important source modifications preserved here

### `supersplat-viewer`

The viewer was modified locally and those changes are intentionally packaged in this repo. Most importantly:

- settings schema now supports gradient backgrounds
- runtime viewer logic applies gradient CSS backgrounds and transparent clear colors
- content transform support was added
- voxel collider, walk, and fly behavior were adjusted for the local scene workflows

### `splat-transform`

The transform tool was also modified locally. The main change preserved here is:

- the CLI now errors when per-file transform flags such as `-r` and `-t` are written before the input file instead of after it

## Packaging strategy chosen in the thread

- mono-repo layout
- include modified `supersplat-viewer` source
- include modified `splat-transform` source
- include a repo-local Codex plugin and skill
- include `dist/`
- exclude `node_modules/`
- keep only `baoan` and `dashi` demo assets inside `public/`

## Why this summary exists

The local Codex state exposes thread metadata and prompts, but not a convenient, directly exportable full-fidelity transcript file for this thread. For repo packaging, the chosen approach is to preserve a structured implementation summary instead of attempting a brittle raw transcript dump.
