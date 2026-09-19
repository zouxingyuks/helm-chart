"""Verify Docker-loaded offline images against the release image IDs and platform.

For Kubernetes/containerd also check import on each schedulable node; the Docker
image store is not automatically shared with the Kubernetes CRI runtime.
"""
import argparse
import json
import pathlib
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("manifest", type=pathlib.Path)
args = parser.parse_args()
manifest = json.loads(args.manifest.read_text())
if manifest["mode"] != "offline":
    raise SystemExit("This check requires an offline release manifest with image IDs")
for image in manifest["images"]:
    actual = json.loads(subprocess.check_output(["docker", "image", "inspect", image["reference"]], text=True))[0]
    if actual["Id"] != image["id"]:
        raise SystemExit("Image ID mismatch: " + image["reference"])
    if actual["Os"] + "/" + actual["Architecture"] != manifest["platform"]:
        raise SystemExit("Wrong platform: " + image["reference"])
    print("PASS", image["reference"])
