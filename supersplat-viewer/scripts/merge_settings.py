#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


def load_json(path: Path):
    return json.loads(path.read_text())


def build_fov_track(times, fov):
    return [fov] * len(times)


def normalize_tracks(v1, fov):
    normalized_tracks = []
    for track in v1.get("animTracks", []):
        next_track = dict(track)
        keyframes = dict(next_track.get("keyframes", {}))
        values = dict(keyframes.get("values", {}))
        times = keyframes.get("times", [])
        values["fov"] = build_fov_track(times, fov)
        keyframes["values"] = values
        next_track["keyframes"] = keyframes
        normalized_tracks.append(next_track)
    return normalized_tracks


def camera_initial(v1):
    camera = v1.get("camera", {})
    return {
        "position": camera.get("position"),
        "target": camera.get("target"),
        "fov": camera.get("fov", 75),
    }


def convert_v1_to_v2(v1_path: Path):
    v1 = load_json(v1_path)
    initial = camera_initial(v1)
    fov = initial["fov"]
    return {
        "version": 2,
        "tonemapping": "none",
        "highPrecisionRendering": False,
        "background": {
            "color": (v1.get("background", {}).get("color") or [0, 0, 0]),
        },
        "postEffectSettings": {
            "sharpness": {
                "enabled": False,
                "amount": 0,
            },
            "bloom": {
                "enabled": False,
                "intensity": 1,
                "blurLevel": 2,
            },
            "grading": {
                "enabled": False,
                "brightness": 0,
                "contrast": 1,
                "saturation": 1,
                "tint": [1, 1, 1],
            },
            "vignette": {
                "enabled": False,
                "intensity": 0.5,
                "inner": 0.3,
                "outer": 0.75,
                "curvature": 1,
            },
            "fringing": {
                "enabled": False,
                "intensity": 0.5,
            },
        },
        "animTracks": normalize_tracks(v1, fov),
        "cameras": [{
            "initial": initial,
        }] if initial["position"] and initial["target"] else [],
        "annotations": [],
        "startMode": "animTrack" if v1.get("camera", {}).get("startAnim") == "animTrack" else "default",
        "hasStartPose": True,
    }


def merge_settings(v1_path: Path, v2_path: Path):
    v1 = load_json(v1_path)
    v2 = load_json(v2_path)

    merged = dict(v2)
    merged["background"] = v1.get("background", v2.get("background"))
    merged["startMode"] = "animTrack"
    merged["hasStartPose"] = True

    cameras = merged.get("cameras") or [{}]
    if not cameras:
        cameras = [{}]
    cameras[0] = dict(cameras[0])
    cameras[0]["initial"] = camera_initial(v1)
    merged["cameras"] = cameras

    merged["animTracks"] = normalize_tracks(v1, cameras[0]["initial"]["fov"])
    return merged


def main():
    parser = argparse.ArgumentParser(
        description="Merge a v1 settings.json with a v2 settings JSON, or convert a v1 settings.json to v2."
    )
    parser.add_argument("v1_settings", type=Path, help="Path to the simple v1 settings.json")
    parser.add_argument("output", type=Path, help="Path to write the merged JSON")
    parser.add_argument(
        "--base-v2",
        dest="v2_settings",
        type=Path,
        help="Optional path to the base version 2 settings JSON",
    )
    args = parser.parse_args()

    if args.v2_settings:
        merged = merge_settings(args.v1_settings, args.v2_settings)
    else:
        merged = convert_v1_to_v2(args.v1_settings)
    args.output.write_text(json.dumps(merged, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
