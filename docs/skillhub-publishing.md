# Skill Publishing Notes / SkillHub 发布说明

This repo is prepared for two publishing shapes:

- Codex plugin: `plugins/splat-transform-for-lcc/`
- Standalone skill: `skills/supersplat-workflow/SKILL.md`

The standalone path mirrors the plugin skill so platforms that expect a repository-level `skills/` directory can discover it without understanding Codex plugin metadata.

## Skill value / skill 的价值

This skill helps users convert LCC/PLY Gaussian splat scenes into deployable SuperSplat viewer assets. It explains the domain terms, chooses precision-preserving defaults, and prevents common coordinate mistakes across `splat-transform` 1.9.2 and 2.x.

中文说明：这个 skill 面向需要把 LCC/PLY 高斯泼溅资产交付到 SuperSplat viewer 的用户。它不只是命令集合，还解释 LCC、SuperSplat、SOG、streamed LOD、voxel 等概念，说明什么时候应该用 PLY 保精度、什么时候应该用 LCC 保多层级流式加载。

## Terminology to keep in listing text / 发布页应保留的名词解释

- `LCC`: XGRIDS/其域场景容器。适合作为真实多层级 streamed LOD 来源，但可能已经有压缩/量化。
- `SuperSplat`: PlayCanvas 高斯泼溅编辑器/查看器生态，是本仓库输出资产的目标 viewer。
- `PLY`: 原始训练输出或高斯属性文件。通常精度最高，推荐用于生成 `scene.sog` 和 voxel。
- `SOG`: SuperSplat 使用的紧凑高斯泼溅资产格式。
- `streamed LOD`: 以 `lod-meta.json` 为入口的流式多层级输出，用于大场景渐进加载。
- `voxel`: `walk.voxel.json`/`walk.voxel.bin` 体素碰撞数据，用于行走和碰撞。
- `splat-transform`: 转换 CLI。本 repo 包含 1.9.2 和 2.1.1，因为 2.x 的 LCC reader 和 voxel 参数不同。

## SkillHub CLI flow

The CLI advertises a direct `publish` command that accepts a `SKILL.md` path, tags, visibility, and GitHub repo URL:

```bash
npx @skills-hub-ai/cli login
npx @skills-hub-ai/cli publish skills/supersplat-workflow/SKILL.md \
  --github-repo https://github.com/Shuang-su/splat-transform_for_lcc \
  --tags supersplat,lcc,sog,ply,voxel,gaussian-splatting,zh-CN
```

Use `--draft` first if you want to review the listing before public release:

```bash
npx @skills-hub-ai/cli publish skills/supersplat-workflow/SKILL.md \
  --draft \
  --github-repo https://github.com/Shuang-su/splat-transform_for_lcc \
  --tags supersplat,lcc,sog,ply,voxel,gaussian-splatting,zh-CN
```

Actual publication requires an authenticated SkillHub account. If the local machine is not logged in, run `npx @skills-hub-ai/cli login` or use the SkillHub web flow.

## Codex Marketplace / other platforms

Use the GitHub repository URL as the public source:

```text
https://github.com/Shuang-su/splat-transform_for_lcc
```

Recommended listing summary:

```text
Bilingual LCC/PLY to SuperSplat workflow. Converts Gaussian splat scenes into SOG, streamed LOD, voxel collision data, merged settings, and local viewer routes while explaining LCC, SuperSplat, SOG, streamed LOD, voxel, and version-specific coordinate defaults.
```

Recommended Chinese summary:

```text
中英双语 LCC/PLY 转 SuperSplat 工作流。用于生成 SOG、streamed LOD、体素碰撞、合并 settings 并挂载本地 viewer route，同时解释 LCC、SuperSplat、SOG、streamed LOD、voxel 和 1.9.2/2.x 坐标差异。
```

## Release checklist

1. Keep `plugins/splat-transform-for-lcc/skills/supersplat-workflow/SKILL.md` and `skills/supersplat-workflow/SKILL.md` in sync.
2. Validate JSON metadata:

```bash
python3 -m json.tool plugins/splat-transform-for-lcc/.codex-plugin/plugin.json >/dev/null
python3 -m json.tool .agents/plugins/marketplace.json >/dev/null
```

3. Validate the workflow script:

```bash
python3 -m py_compile plugins/splat-transform-for-lcc/scripts/scene_workflow.py
```

4. Commit and push to GitHub.
5. Publish with authenticated SkillHub CLI or submit the GitHub URL through the target platform UI.
