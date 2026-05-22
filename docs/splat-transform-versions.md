# splat-transform Version Notes

This repo keeps two `splat-transform` source trees because the LCC workflow changed materially between 1.9.2 and 2.x.

## Included versions

- `splat-transform-1.9.2/`
  Legacy reference used by the original workflow. Keep this for reproducing older scene outputs.
- `splat-transform-2.1.1/`
  Current default source for new conversions. The workflow scripts prefer this path when `--splat-transform` is not provided.

Both folders omit `node_modules`; generated build output may also need to be rebuilt after a fresh clone. Run `npm install` inside the selected folder before building or running local tests.

## Behavioral differences that affect this workflow

- LCC coordinate handling changed in 2.x. The 2.1.1 LCC reader marks LCC data with an internal `90,0,180` source transform, so new LCC streamed output should not also receive the old default `-r 90,0,0`.
- PLY coordinate handling did not receive that LCC-specific correction. For this project, PLY-derived SOG output still uses `input.ply -r 90,0,0 output/scene.sog`.
- Voxel CLI parameters changed. Version 1.9.2 uses `-R 0.08 -A 0.20`; version 2.1.1 uses `--voxel-params 0.08,0.20`.
- PLY-derived 2.x voxel output uses baked rotation: `--voxel-params 0.08,0.20 input.ply -r -90,0,180 output/walk.voxel.json`.
- `meta.json.version: 2` is an output format version, not the CLI version.

## Recommended default

Use original PLY as the source for SOG and voxel when it is available. Use LCC for true multi-LOD streamed output. Use PLY for streamed output only when single-layer LOD is acceptable or the PLY already has a `lod` column.
