# splat-transform-workflow-for-lcc

[English](#english) | [中文](#中文)

## English

This repository packages a reusable LCC/PLY-to-SuperSplat workflow. It is designed for converting Gaussian splat scenes into assets that can be loaded by a SuperSplat viewer, while preserving precision and keeping streamed LOD, SOG, voxel collision data, and viewer settings aligned.

### What It Includes

- A modified `supersplat-viewer` source tree
- Versioned `splat-transform` source trees for legacy 1.9.2 and current 2.1.1 workflows
- A repo-local Codex plugin and skill
- A top-level standalone skill copy for agents that scan `skills/`
- Helper scripts for scene conversion, settings merge, and viewer mounting
- Two ready-to-open demo routes: `baoan` and `dashi`

### Repository Layout

```text
splat-transform-workflow-for-lcc/
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
│           └── splat-transform-workflow-for-lcc/
├── skills/
│   └── splat-transform-workflow-for-lcc/
├── splat-transform-1.9.2/
├── splat-transform-2.1.1/
└── supersplat-viewer/
```

### Why This Workflow Exists

Raw conversion commands are easy to get wrong because visual splats, streamed assets, and voxel collision data may need different source formats and rotations. This workflow provides a consistent path:

- Use original PLY for high-precision SOG and voxel output when available.
- Use LCC for true streamed multi-LOD output.
- Preserve viewer settings and route wiring so the scene can open directly in `supersplat-viewer`.
- Apply version-aware rotations so visual splats and walkable voxel collision stay aligned.

### Glossary

- `LCC`: XGRIDS/其域 scene container. In this workflow it is mainly used as the source for true streamed multi-LOD output. It may contain multiple LOD levels and environment data, but its attributes may already be compressed or quantized.
- `SuperSplat`: PlayCanvas Gaussian splat editor/viewer ecosystem. The output of this repository is intended for SuperSplat viewer assets and routes.
- `PLY`: Common training output or raw Gaussian attribute file. It usually preserves float32 attributes and is preferred for high-precision `scene.sog` and `walk.voxel.json` generation.
- `SOG`: Super-compressed Gaussian splat, a compact SuperSplat asset format. Common outputs are `scene.sog` or `meta.json` plus binary chunks.
- `streamed LOD`: Progressive level-of-detail output centered on `lod-meta.json`, useful for loading large scenes gradually.
- `voxel`: Collision data, usually `walk.voxel.json` plus `walk.voxel.bin`. It is used for walking and collision, not for visual splat rendering.
- `splat-transform`: Conversion CLI. This repo keeps both `splat-transform-1.9.2/` and `splat-transform-2.1.1/` because LCC coordinate handling and voxel parameters changed in 2.x.
- `LOD0`: The finest main LOD level, often used as the legacy LCC voxel source.
- `meta.json.version`: Output data format version, not the `splat-transform` CLI version.

### splat-transform Versions

This repo keeps both transform sources intentionally:

- `splat-transform-1.9.2/` is the legacy reference used by the original workflow.
- `splat-transform-2.1.1/` is the default for new conversions and is preferred by `scene_workflow.py` when `--splat-transform` is omitted.

The important workflow difference is that `splat-transform` 2.x reads LCC with an internal `90,0,180` source transform. Do not add the old LCC `-r 90,0,0` on top of 2.x LCC streamed output. PLY does not use that LCC-specific correction; in this workflow, 2.x PLY-derived SOG and PLY-derived streamed LOD use baked `-r -90,0,0`:

```bash
input.ply -r -90,0,0 output/scene.sog
input.ply -l 0 -r -90,0,0 output/lod-meta.json
```

More detail is recorded in [docs/splat-transform-versions.md](docs/splat-transform-versions.md).

### Default Workflow

The end-to-end command is:

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py deploy-scene ...
```

By default it:

- Converts an `.lcc` scene into streamed LOD output
- Generates `scene.sog` from original PLY when `--sog-input` is provided
- Generates voxel collision data from original PLY when `--voxel-input` is provided
- Merges settings into a version 2 viewer JSON
- Mounts the result into a local `supersplat-viewer/public/<scene>` route

### Parameter Meanings

- `--stream-rotation auto`
  LCC on 2.x uses no extra `-r`; PLY on 2.x uses `-90,0,0`; legacy LCC and PLY use `90,0,0`.
- `--sog-rotation auto`
  PLY on 2.x uses `-90,0,0`; LCC on 2.x uses no extra `-r`; legacy PLY uses `90,0,0`.
- `--voxel-rotation auto`
  PLY on 2.x uses `-90,0,180`; LCC on 2.x uses `0,0,180`; legacy inputs use `90,0,0`.
- `--voxel-lod 0`
  Selects the legacy LCC voxel source level when voxel input is LCC.
- `--voxel-resolution 0.08`
  Voxel size in meters. Smaller values are more precise but produce larger files and heavier collision data.
- `--voxel-alpha 0.20`
  Alpha threshold for voxelization. Higher values ignore more weak or semi-transparent edges.

Per-file `splat-transform` transforms must be written after the input file they apply to:

```bash
node splat-transform-2.1.1/bin/cli.mjs input.ply -r -90,0,0 output/scene.sog
```

Current 2.x defaults:

```text
LCC -> streamed: no extra -r
PLY -> SOG:      -r -90,0,0
PLY -> streamed: -r -90,0,0
PLY -> voxel:    -r -90,0,180
LCC -> voxel:    -r 0,0,180
```

### Common Commands

Merge settings:

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py merge-settings \
  /path/to/settings.json \
  /path/to/settings-merged.json \
  --base-v2 /path/to/settings-v2.json
```

Convert scene assets:

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

Full deploy:

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

### Install on Another Machine

1. Clone this repo.
2. Open the repo as a Codex workspace so the repo-local plugin marketplace is visible.
3. Optionally install the skill globally:

```bash
./install_skill.sh
```

This creates a symlink at `~/.codex/skills/splat-transform-workflow-for-lcc`.

Make sure the machine has:

- `python3`
- `node`
- Local dependencies installed for the copied `supersplat-viewer` and whichever `splat-transform-*` version you run

### Skill Files

The repo-local plugin skill is stored at:

```text
plugins/splat-transform-for-lcc/skills/splat-transform-workflow-for-lcc/SKILL.md
```

The same content is mirrored for tools that scan a repo-level `skills/` directory:

```text
skills/splat-transform-workflow-for-lcc/SKILL.md
```

### Included Demos

- `supersplat-viewer/public/baoan/`
- `supersplat-viewer/public/dashi/`

These are kept as cross-machine smoke tests and reference routes.

### More Documentation

- [docs/workflow-reference.md](docs/workflow-reference.md)
- [docs/splat-transform-versions.md](docs/splat-transform-versions.md)
- [docs/thread-summary.md](docs/thread-summary.md)

## 中文

这个仓库封装了一套可复用的 LCC/PLY 转 SuperSplat 工作流，用于把高斯泼溅场景转换成 SuperSplat viewer 可加载的资产，并保持视觉资产、流式 LOD、SOG、体素碰撞数据和 viewer 配置对齐。

### 包含内容

- 修改过的 `supersplat-viewer` 源码树
- 两套版本化 `splat-transform` 源码：旧流程参考 `1.9.2` 和当前默认 `2.1.1`
- 仓库内 Codex plugin 和 skill
- 供智能体扫描的顶层 `skills/` skill 副本
- 场景转换、settings 合并和 viewer 挂载脚本
- 两个可直接打开的 demo route：`baoan` 和 `dashi`

### 仓库结构

```text
splat-transform-workflow-for-lcc/
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
│           └── splat-transform-workflow-for-lcc/
├── skills/
│   └── splat-transform-workflow-for-lcc/
├── splat-transform-1.9.2/
├── splat-transform-2.1.1/
└── supersplat-viewer/
```

### 这个工作流解决什么问题

直接手写转换命令很容易出错，因为视觉 splat、流式资产和体素碰撞数据可能需要不同的输入源和旋转参数。这个工作流提供一条一致路径：

- 有原始 PLY 时，用 PLY 生成高精度 SOG 和 voxel。
- 需要真正多层级渐进加载时，用 LCC 生成 streamed LOD。
- 保留 viewer settings 和 route wiring，让场景可以直接在 `supersplat-viewer` 中打开。
- 根据 `splat-transform` 版本和输入格式自动选择 rotation，使视觉内容和可行走 voxel collision 对齐。

### 名词解释

- `LCC`：XGRIDS/其域场景容器。这里主要把它作为真实 streamed multi-LOD 的来源；它可以包含多层 LOD 和环境层，但属性可能已经被压缩或量化。
- `SuperSplat`：PlayCanvas 的高斯泼溅编辑器/查看器生态。本仓库输出的资产和 route 面向 SuperSplat viewer。
- `PLY`：常见训练输出或原始高斯属性文件。通常保留 float32 属性，适合作为高精度 `scene.sog` 和 `walk.voxel.json` 的来源。
- `SOG`：Super-compressed Gaussian splat，是 SuperSplat 使用的紧凑资产格式，常见输出为 `scene.sog` 或 `meta.json` 加二进制块。
- `streamed LOD`：以 `lod-meta.json` 为入口的流式多层级输出，适合大场景渐进加载。
- `voxel`：体素碰撞数据，通常是 `walk.voxel.json` 加 `walk.voxel.bin`，用于行走和碰撞，不是视觉 splat 本身。
- `splat-transform`：格式转换 CLI。本仓库保留 `splat-transform-1.9.2/` 和 `splat-transform-2.1.1/`，因为 2.x 修改了 LCC 坐标处理和 voxel 参数。
- `LOD0`：最精细主层级，旧 LCC voxel 流程里常作为体素来源。
- `meta.json.version`：输出数据格式版本，不是 `splat-transform` CLI 版本。

### splat-transform 版本

这个仓库有意保留两套 `splat-transform`：

- `splat-transform-1.9.2/` 是旧流程的复现参考。
- `splat-transform-2.1.1/` 是新转换的默认版本；没有显式传 `--splat-transform` 时，`scene_workflow.py` 会优先使用它。

关键差异是：`splat-transform` 2.x 的 LCC reader 内部带 `90,0,180` source transform。因此 2.x LCC streamed 输出不要再叠加旧的 `-r 90,0,0`。PLY 不适用这个 LCC 专属修正；本工作流里，2.x PLY 生成 SOG 和 PLY 生成 streamed LOD 都使用烘焙外参 `-r -90,0,0`：

```bash
input.ply -r -90,0,0 output/scene.sog
input.ply -l 0 -r -90,0,0 output/lod-meta.json
```

更多细节见 [docs/splat-transform-versions.md](docs/splat-transform-versions.md)。

### 默认工作流

端到端命令入口是：

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py deploy-scene ...
```

默认会执行：

- 将 `.lcc` 场景转换为 streamed LOD 输出
- 如果提供 `--sog-input`，从原始 PLY 生成 `scene.sog`
- 如果提供 `--voxel-input`，从原始 PLY 生成体素碰撞数据
- 将 settings 合并为 version 2 viewer JSON
- 将结果挂载到本地 `supersplat-viewer/public/<scene>` route

### 参数含义

- `--stream-rotation auto`
  2.x LCC 不额外加 `-r`；2.x PLY 使用 `-90,0,0`；legacy LCC 和 PLY 使用 `90,0,0`。
- `--sog-rotation auto`
  2.x PLY 使用 `-90,0,0`；2.x LCC 不额外加 `-r`；legacy PLY 使用 `90,0,0`。
- `--voxel-rotation auto`
  2.x PLY 使用 `-90,0,180`；2.x LCC 使用 `0,0,180`；legacy 输入使用 `90,0,0`。
- `--voxel-lod 0`
  当 voxel 输入是 LCC 时，选择旧流程里的 LCC 体素来源层级。
- `--voxel-resolution 0.08`
  体素大小，单位为米。值越小越精细，但文件更大、碰撞数据更重。
- `--voxel-alpha 0.20`
  体素化 alpha 阈值。值越高，会忽略更多弱透明边缘。

`splat-transform` 的单文件 transform 参数必须写在对应 input 文件后面：

```bash
node splat-transform-2.1.1/bin/cli.mjs input.ply -r -90,0,0 output/scene.sog
```

当前 2.x 默认参数表：

```text
LCC -> streamed: 不额外加 -r
PLY -> SOG:      -r -90,0,0
PLY -> streamed: -r -90,0,0
PLY -> voxel:    -r -90,0,180
LCC -> voxel:    -r 0,0,180
```

### 常用命令

合并 settings：

```bash
python3 plugins/splat-transform-for-lcc/scripts/scene_workflow.py merge-settings \
  /path/to/settings.json \
  /path/to/settings-merged.json \
  --base-v2 /path/to/settings-v2.json
```

只转换场景资产：

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

完整部署：

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

### 在其他机器安装

1. Clone 本仓库。
2. 将本仓库作为 Codex workspace 打开，这样仓库内 plugin marketplace 可见。
3. 可选：全局安装 skill：

```bash
./install_skill.sh
```

这会创建指向 `~/.codex/skills/splat-transform-workflow-for-lcc` 的 symlink。

机器需要具备：

- `python3`
- `node`
- `supersplat-viewer` 和所选 `splat-transform-*` 版本需要的本地依赖

### Skill 文件

仓库内 plugin skill 位于：

```text
plugins/splat-transform-for-lcc/skills/splat-transform-workflow-for-lcc/SKILL.md
```

供扫描顶层 `skills/` 的工具使用的副本位于：

```text
skills/splat-transform-workflow-for-lcc/SKILL.md
```

### 内置 Demo

- `supersplat-viewer/public/baoan/`
- `supersplat-viewer/public/dashi/`

这些 demo 用作跨机器 smoke test 和参考 route。

### 更多文档

- [docs/workflow-reference.md](docs/workflow-reference.md)
- [docs/splat-transform-versions.md](docs/splat-transform-versions.md)
- [docs/thread-summary.md](docs/thread-summary.md)
