#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from merge_settings import convert_v1_to_v2, merge_settings  # noqa: E402


def run(cmd, env=None):
    print("+", " ".join(shlex.quote(part) for part in cmd))
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


def slug_value(value: str) -> str:
    return value.replace(",", "_")


def lod_dir_name(rotation: str, translate: str | None, remove_environment: bool) -> str:
    prefix = "supersplat_lod_noenv_" if remove_environment else "supersplat_lod_"
    name = prefix + "rot" + slug_value(rotation)
    if translate:
        name += "_trans" + slug_value(translate)
    return name


def voxel_dir_name(voxel_lod: int, voxel_resolution: float, voxel_alpha: float, rotation: str, translate: str | None) -> str:
    name = f"voxel_lod{voxel_lod}_r{voxel_resolution:.2f}_a{voxel_alpha:.2f}_rot{slug_value(rotation)}"
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
    input_lcc = Path(args.input_lcc).expanduser().resolve()
    output_root = Path(args.output_root).expanduser().resolve()
    output_root.mkdir(parents=True, exist_ok=True)

    streamed_dir = output_root / lod_dir_name(args.rotation, args.translate, args.remove_environment)
    voxel_dir = output_root / voxel_dir_name(
        args.voxel_lod,
        args.voxel_resolution,
        args.voxel_alpha,
        args.rotation,
        args.translate,
    )

    lod_meta = streamed_dir / "lod-meta.json"
    voxel_json = voxel_dir / f"{input_lcc.stem}.voxel.json"

    env = os.environ.copy()
    if args.node_memory:
        env["NODE_OPTIONS"] = f"--max-old-space-size={args.node_memory}"

    lod_cmd = ["node", str(cli), "-w", str(input_lcc), "-r", args.rotation]
    if args.translate:
        lod_cmd += ["-t", args.translate]
    lod_cmd += [str(lod_meta)]
    run(lod_cmd, env=env)

    if args.remove_environment:
        strip_environment(streamed_dir)

    voxel_cmd = [
        "node",
        str(cli),
        "-w",
        "-O",
        str(args.voxel_lod),
        "-R",
        str(args.voxel_resolution),
        "-A",
        str(args.voxel_alpha),
        str(input_lcc),
        "-r",
        args.rotation,
    ]
    if args.translate:
        voxel_cmd += ["-t", args.translate]
    voxel_cmd += [str(voxel_json)]
    run(voxel_cmd, env=env)

    print(f"streamed_lod={lod_meta}")
    print(f"voxel_json={voxel_json}")
    print(f"voxel_bin={voxel_bin_from_json(voxel_json)}")
    return streamed_dir, voxel_json


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

    if args.base_v2:
        merged = merge_settings(v1_settings, Path(args.base_v2).expanduser().resolve())
    else:
        merged = convert_v1_to_v2(v1_settings)
    write_json(settings_output, merged)

    streamed_dir, voxel_json = convert_scene(args)

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
    print(f"route={route_dir}")


def build_parser():
    parser = argparse.ArgumentParser(
        description=(
            "Reusable SuperSplat scene workflow. Default deploy values are: "
            "rotation=90,0,0, voxel-lod=0, voxel-resolution=0.08, voxel-alpha=0.20."
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
        help="Generate streamed LOD and LOD0 voxel output from an LCC scene.",
    )
    convert_parser.add_argument("input_lcc")
    convert_parser.add_argument("output_root")
    convert_parser.add_argument("--splat-transform", default=os.environ.get("SPLAT_TRANSFORM_DIR", "~/Documents/splat-transform"))
    convert_parser.add_argument("--rotation", default="90,0,0", help="Scene rotation, default: 90,0,0")
    convert_parser.add_argument("--translate", help="Optional scene translation")
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
        help="Merge settings, convert the scene, and mount a viewer route with the default LCC workflow.",
    )
    deploy_parser.add_argument("scene_key")
    deploy_parser.add_argument("input_lcc")
    deploy_parser.add_argument("output_root")
    deploy_parser.add_argument("viewer_public")
    deploy_parser.add_argument("v1_settings")
    deploy_parser.add_argument("--base-v2")
    deploy_parser.add_argument("--settings-output")
    deploy_parser.add_argument("--title")
    deploy_parser.add_argument("--splat-transform", default=os.environ.get("SPLAT_TRANSFORM_DIR", "~/Documents/splat-transform"))
    deploy_parser.add_argument("--rotation", default="90,0,0", help="Scene rotation, default: 90,0,0")
    deploy_parser.add_argument("--translate", help="Optional scene translation")
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
    deploy_parser.set_defaults(func=deploy_scene)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
