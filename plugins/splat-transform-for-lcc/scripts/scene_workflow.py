#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
sys.path.insert(0, str(SCRIPT_DIR))

from merge_settings import convert_v1_to_v2, merge_settings  # noqa: E402


def run(cmd, env=None, dry_run=False):
    print("+", " ".join(shlex.quote(part) for part in cmd))
    if dry_run:
        return
    subprocess.run(cmd, check=True, env=env)


def load_json(path: Path):
    return json.loads(path.read_text())


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")


def resolve_cli(path_value: str) -> Path:
    base = Path(path_value).expanduser().resolve()
    cli = base / "bin" / "cli.mjs" if base.is_dir() else base
    if not cli.exists():
        raise FileNotFoundError(f"splat-transform CLI not found: {cli}")
    return cli


def default_splat_transform_dir() -> str:
    env_value = os.environ.get("SPLAT_TRANSFORM_DIR")
    if env_value:
        return env_value

    repo_local = REPO_ROOT / "splat-transform-2.1.1"
    if repo_local.exists():
        return str(repo_local)

    return "~/Documents/splat-transform"


def cli_root(cli: Path) -> Path:
    if cli.name == "cli.mjs" and cli.parent.name == "bin":
        return cli.parent.parent
    return cli.parent


def parse_major_version(text: str) -> int | None:
    match = re.search(r"\bv?(\d+)\.(\d+)\.(\d+)\b", text)
    return int(match.group(1)) if match else None


def detect_splat_transform_major(cli: Path, override: str, env) -> int:
    if override != "auto":
        return int(override)

    try:
        result = subprocess.run(
            ["node", str(cli), "--version"],
            check=True,
            capture_output=True,
            text=True,
            env=env,
        )
        major = parse_major_version(result.stdout + result.stderr)
        if major is not None:
            return major
    except subprocess.CalledProcessError:
        pass

    package_json = cli_root(cli) / "package.json"
    if package_json.exists():
        major = parse_major_version(load_json(package_json).get("version", ""))
        if major is not None:
            return major

    raise RuntimeError(f"Unable to detect splat-transform major version for {cli}")


def path_kind(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".lcc":
        return "lcc"
    if suffix == ".ply":
        return "ply"
    return suffix[1:] or "input"


def slug_value(value: str | None) -> str:
    if value is None:
        return "none"
    return value.replace(",", "_")


def rotation_label(value: str | None) -> str:
    return "rot_none" if value is None else "rot" + slug_value(value)


def fmt_float(value: float) -> str:
    return f"{value:.2f}"


def effective_rotation(value: str, source_kind: str, output_kind: str, major: int) -> str | None:
    lowered = value.lower()
    if lowered == "none":
        return None
    if lowered != "auto":
        return value

    if output_kind == "voxel":
        if major >= 2:
            return "-90,0,180" if source_kind == "ply" else None
        return "90,0,0"

    if source_kind == "lcc" and major >= 2:
        return None
    if source_kind == "ply" and major == 2 and output_kind in {"stream", "sog"}:
        return "-90,0,0"
    return "90,0,0"


def append_transform_actions(cmd: list[str], rotation: str | None, translate: str | None):
    if rotation:
        cmd += ["-r", rotation]
    if translate:
        cmd += ["-t", translate]


def stream_dir_name(source_kind: str, rotation: str | None, translate: str | None, remove_environment: bool) -> str:
    prefix = "streamed_noenv" if remove_environment else "streamed"
    name = f"{prefix}_{source_kind}_{rotation_label(rotation)}"
    if translate:
        name += "_trans" + slug_value(translate)
    return name


def sog_dir_name(source_kind: str, rotation: str | None, translate: str | None) -> str:
    name = f"sog_{source_kind}_{rotation_label(rotation)}"
    if translate:
        name += "_trans" + slug_value(translate)
    return name


def voxel_dir_name(source_kind: str, voxel_lod: int, voxel_resolution: float, voxel_alpha: float, rotation: str | None, translate: str | None) -> str:
    baked = f"baked-r{slug_value(rotation)}" if rotation else "identity"
    name = (
        f"voxel_{source_kind}_lod{voxel_lod}_"
        f"r{fmt_float(voxel_resolution)}_a{fmt_float(voxel_alpha)}_{baked}"
    )
    if translate:
        name += "_trans" + slug_value(translate)
    return name


def strip_environment(streamed_dir: Path):
    lod_meta = streamed_dir / "lod-meta.json"
    data = load_json(lod_meta)
    data["environment"] = None
    write_json(lod_meta, data)
    env_dir = streamed_dir / "env"
    if env_dir.exists():
        shutil.rmtree(env_dir)


def voxel_bin_from_json(voxel_json: Path) -> Path:
    name = voxel_json.name
    if not name.endswith(".voxel.json"):
        raise ValueError(f"Expected a .voxel.json file: {voxel_json}")
    return voxel_json.with_name(name.replace(".voxel.json", ".voxel.bin"))


def convert_scene(args):
    cli = resolve_cli(args.splat_transform)
    stream_input = Path(args.stream_input).expanduser().resolve()
    sog_input = Path(args.sog_input).expanduser().resolve() if args.sog_input else stream_input
    voxel_input = Path(args.voxel_input).expanduser().resolve() if args.voxel_input else sog_input
    output_root = Path(args.output_root).expanduser().resolve()
    if not args.dry_run:
        output_root.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    if args.node_memory:
        env["NODE_OPTIONS"] = f"--max-old-space-size={args.node_memory}"

    major = detect_splat_transform_major(cli, args.splat_transform_major, env)
    stream_kind = path_kind(stream_input)
    sog_kind = path_kind(sog_input)
    voxel_kind = path_kind(voxel_input)

    stream_rotation = effective_rotation(args.stream_rotation, stream_kind, "stream", major)
    sog_rotation = effective_rotation(args.sog_rotation, sog_kind, "sog", major)
    voxel_rotation = effective_rotation(args.voxel_rotation, voxel_kind, "voxel", major)

    streamed_dir = output_root / stream_dir_name(stream_kind, stream_rotation, args.translate, args.remove_environment)
    sog_dir = output_root / sog_dir_name(sog_kind, sog_rotation, args.translate)
    voxel_dir = output_root / voxel_dir_name(
        voxel_kind,
        args.voxel_lod,
        args.voxel_resolution,
        args.voxel_alpha,
        voxel_rotation,
        args.translate,
    )

    lod_meta = streamed_dir / "lod-meta.json"
    sog_output = sog_dir / "scene.sog"
    voxel_json = voxel_dir / "walk.voxel.json"

    stream_cmd = ["node", str(cli), "-w", str(stream_input)]
    if stream_kind == "ply" and args.stream_ply_lod.lower() != "none":
        stream_cmd += ["-l", args.stream_ply_lod]
    append_transform_actions(stream_cmd, stream_rotation, args.translate)
    stream_cmd += [str(lod_meta)]
    run(stream_cmd, env=env, dry_run=args.dry_run)

    if args.remove_environment:
        if args.dry_run:
            print(f"would_strip_environment={streamed_dir}")
        else:
            strip_environment(streamed_dir)

    sog_cmd = ["node", str(cli), "-w", str(sog_input)]
    append_transform_actions(sog_cmd, sog_rotation, args.translate)
    sog_cmd += [str(sog_output)]
    run(sog_cmd, env=env, dry_run=args.dry_run)

    voxel_cmd = ["node", str(cli), "-w"]
    if major >= 2:
        if voxel_kind == "lcc":
            voxel_cmd += ["--lod-select", str(args.voxel_lod)]
        voxel_cmd += ["--voxel-params", f"{fmt_float(args.voxel_resolution)},{fmt_float(args.voxel_alpha)}"]
    else:
        if voxel_kind == "lcc":
            voxel_cmd += ["-O", str(args.voxel_lod)]
        voxel_cmd += ["-R", fmt_float(args.voxel_resolution), "-A", fmt_float(args.voxel_alpha)]
    voxel_cmd += [str(voxel_input)]
    append_transform_actions(voxel_cmd, voxel_rotation, args.translate)
    voxel_cmd += [str(voxel_json)]
    run(voxel_cmd, env=env, dry_run=args.dry_run)

    print(f"splat_transform_major={major}")
    print(f"streamed_lod={lod_meta}")
    print(f"sog={sog_output}")
    print(f"voxel_json={voxel_json}")
    print(f"voxel_bin={voxel_bin_from_json(voxel_json)}")
    return streamed_dir, voxel_json, sog_output


def mount_viewer(args):
    scene_key = args.scene_key
    viewer_public = Path(args.viewer_public).expanduser().resolve()
    settings_path = Path(args.settings).expanduser().resolve()
    lod_dir = Path(args.lod_dir).expanduser().resolve()
    voxel_json = Path(args.voxel_json).expanduser().resolve()
    voxel_bin = voxel_bin_from_json(voxel_json)
    route_dir = viewer_public / scene_key

    if route_dir.exists():
        shutil.rmtree(route_dir)

    (route_dir / "streamed").mkdir(parents=True, exist_ok=True)
    (route_dir / "voxel").mkdir(parents=True, exist_ok=True)

    settings_name = settings_path.name
    shutil.copy2(settings_path, route_dir / settings_name)
    shutil.copytree(lod_dir, route_dir / "streamed", dirs_exist_ok=True)
    shutil.copy2(voxel_json, route_dir / "voxel" / "walk.voxel.json")
    shutil.copy2(voxel_bin, route_dir / "voxel" / "walk.voxel.bin")

    title = args.title or scene_key.replace("-", " ").title()
    viewer_url = (
        f"../?settings={scene_key}/{settings_name}"
        f"&content={scene_key}/streamed/lod-meta.json"
        f"&voxel={scene_key}/voxel/walk.voxel.json"
    )

    index_html = f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} Viewer</title>
  <meta http-equiv="refresh" content="0; url={viewer_url}">
</head>
<body>
  <p>Redirecting to viewer...</p>
  <p>
    If the redirect does not start, open
    <a href="{viewer_url}">the {title} viewer</a>.
  </p>
</body>
</html>
"""
    (route_dir / "index.html").write_text(index_html)

    print(f"viewer_route={route_dir}")
    print(f"viewer_index={route_dir / 'index.html'}")
    return route_dir


def deploy_scene(args):
    v1_settings = Path(args.v1_settings).expanduser().resolve()
    settings_output = Path(args.settings_output).expanduser().resolve() if args.settings_output else None
    if settings_output is None:
        settings_output = v1_settings.parent / ("settings-merged.json" if args.base_v2 else "settings-v2.json")

    if args.dry_run:
        print(f"would_write_settings={settings_output}")
    else:
        if args.base_v2:
            merged = merge_settings(v1_settings, Path(args.base_v2).expanduser().resolve())
        else:
            merged = convert_v1_to_v2(v1_settings)
        write_json(settings_output, merged)

    streamed_dir, voxel_json, sog_output = convert_scene(args)

    if args.dry_run:
        print(f"would_mount_viewer={args.scene_key}")
        print(f"settings={settings_output}")
        print(f"sog={sog_output}")
        return

    mount_args = argparse.Namespace(
        scene_key=args.scene_key,
        viewer_public=args.viewer_public,
        settings=str(settings_output),
        lod_dir=str(streamed_dir),
        voxel_json=str(voxel_json),
        title=args.title,
    )
    route_dir = mount_viewer(mount_args)

    print(f"settings={settings_output}")
    print(f"sog={sog_output}")
    print(f"route={route_dir}")


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Reusable SuperSplat scene workflow. Default deploy values are: "
            "PLY-first SOG/voxel, LCC-first streamed LOD, voxel-resolution=0.08, voxel-alpha=0.20."
        )
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    merge_parser = subparsers.add_parser(
        "merge-settings",
        help="Merge v1 settings with a base v2 settings file, or convert v1 to v2.",
    )
    merge_parser.add_argument("v1_settings")
    merge_parser.add_argument("output")
    merge_parser.add_argument("--base-v2")
    merge_parser.set_defaults(func=lambda args: write_json(
        Path(args.output),
        merge_settings(Path(args.v1_settings), Path(args.base_v2)) if args.base_v2 else convert_v1_to_v2(Path(args.v1_settings)),
    ))

    convert_parser = subparsers.add_parser(
        "convert-scene",
        help="Generate streamed LOD, SOG, and voxel outputs from LCC/PLY inputs.",
    )
    convert_parser.add_argument("stream_input")
    convert_parser.add_argument("output_root")
    convert_parser.add_argument("--sog-input", help="Optional high-precision source for scene.sog; prefer PLY when available.")
    convert_parser.add_argument("--voxel-input", help="Optional high-precision source for walk.voxel.json; prefer PLY when available.")
    convert_parser.add_argument("--splat-transform", default=default_splat_transform_dir())
    convert_parser.add_argument("--splat-transform-major", choices=["auto", "1", "2"], default="auto")
    convert_parser.add_argument(
        "--stream-rotation",
        "--rotation",
        dest="stream_rotation",
        default="auto",
        help="Streamed LOD rotation: auto, none, or x,y,z. --rotation is kept as a legacy alias.",
    )
    convert_parser.add_argument("--sog-rotation", default="auto", help="SOG rotation: auto, none, or x,y,z.")
    convert_parser.add_argument("--voxel-rotation", default="auto", help="Voxel rotation: auto, none, or x,y,z.")
    convert_parser.add_argument("--translate", help="Optional scene translation")
    convert_parser.add_argument(
        "--stream-ply-lod",
        default="0",
        help="LOD tag to add when stream_input is PLY; use 'none' only when the PLY already has a lod column.",
    )
    convert_parser.add_argument("--voxel-lod", type=int, default=0, help="Voxel source LOD, default: 0")
    convert_parser.add_argument(
        "--voxel-resolution",
        type=float,
        default=0.08,
        help="Voxel size in meters, default: 0.08",
    )
    convert_parser.add_argument(
        "--voxel-alpha",
        type=float,
        default=0.20,
        help="Voxel alpha threshold, default: 0.20",
    )
    convert_parser.add_argument("--node-memory", type=int, default=65536)
    convert_parser.add_argument("--remove-environment", action="store_true")
    convert_parser.add_argument("--dry-run", action="store_true", help="Print commands without writing outputs.")
    convert_parser.set_defaults(func=convert_scene)

    mount_parser = subparsers.add_parser("mount-viewer", help="Copy scene outputs into a supersplat-viewer public route.")
    mount_parser.add_argument("scene_key")
    mount_parser.add_argument("viewer_public")
    mount_parser.add_argument("settings")
    mount_parser.add_argument("lod_dir")
    mount_parser.add_argument("voxel_json")
    mount_parser.add_argument("--title")
    mount_parser.set_defaults(func=mount_viewer)

    deploy_parser = subparsers.add_parser(
        "deploy-scene",
        help="Merge settings, convert streamed/SOG/voxel outputs, and mount a viewer route.",
    )
    deploy_parser.add_argument("scene_key")
    deploy_parser.add_argument("stream_input")
    deploy_parser.add_argument("output_root")
    deploy_parser.add_argument("viewer_public")
    deploy_parser.add_argument("v1_settings")
    deploy_parser.add_argument("--base-v2")
    deploy_parser.add_argument("--settings-output")
    deploy_parser.add_argument("--title")
    deploy_parser.add_argument("--sog-input", help="Optional high-precision source for scene.sog; prefer PLY when available.")
    deploy_parser.add_argument("--voxel-input", help="Optional high-precision source for walk.voxel.json; prefer PLY when available.")
    deploy_parser.add_argument("--splat-transform", default=default_splat_transform_dir())
    deploy_parser.add_argument("--splat-transform-major", choices=["auto", "1", "2"], default="auto")
    deploy_parser.add_argument(
        "--stream-rotation",
        "--rotation",
        dest="stream_rotation",
        default="auto",
        help="Streamed LOD rotation: auto, none, or x,y,z. --rotation is kept as a legacy alias.",
    )
    deploy_parser.add_argument("--sog-rotation", default="auto", help="SOG rotation: auto, none, or x,y,z.")
    deploy_parser.add_argument("--voxel-rotation", default="auto", help="Voxel rotation: auto, none, or x,y,z.")
    deploy_parser.add_argument("--translate", help="Optional scene translation")
    deploy_parser.add_argument(
        "--stream-ply-lod",
        default="0",
        help="LOD tag to add when stream_input is PLY; use 'none' only when the PLY already has a lod column.",
    )
    deploy_parser.add_argument("--voxel-lod", type=int, default=0, help="Voxel source LOD, default: 0")
    deploy_parser.add_argument(
        "--voxel-resolution",
        type=float,
        default=0.08,
        help="Voxel size in meters, default: 0.08",
    )
    deploy_parser.add_argument(
        "--voxel-alpha",
        type=float,
        default=0.20,
        help="Voxel alpha threshold, default: 0.20",
    )
    deploy_parser.add_argument("--node-memory", type=int, default=65536)
    deploy_parser.add_argument("--remove-environment", action="store_true")
    deploy_parser.add_argument("--dry-run", action="store_true", help="Print commands without writing outputs.")
    deploy_parser.set_defaults(func=deploy_scene)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
