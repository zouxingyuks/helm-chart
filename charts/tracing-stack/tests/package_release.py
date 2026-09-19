"""Build a complete Helm distribution, optionally including every runtime image.

Requires Helm and PyYAML; --offline also requires Docker. No cluster mutations.
Use an empty output directory; the package always includes all chart dependencies.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import yaml
from build_dependencies import build

CHART = pathlib.Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("output", type=pathlib.Path)
parser.add_argument("--offline", action="store_true", help="Pull and export all runtime and init-container images")
parser.add_argument("--platform", default="linux/amd64", choices=("linux/amd64", "linux/arm64"))
args = parser.parse_args()
out = args.output.resolve()
if out.exists():
    raise SystemExit("Output directory already exists: " + str(out))
build()
out.mkdir(parents=True, exist_ok=False)
subprocess.run(["helm", "lint", str(CHART), "--strict"], check=True)
rendered = subprocess.check_output(["helm", "template", "tracing", str(CHART), "-n", "observability"], text=True)
docs = list(filter(None, yaml.safe_load_all(rendered)))
images = set()
for doc in docs:
    if doc["kind"] in ("Deployment", "StatefulSet", "DaemonSet", "Job", "Pod"):
        spec = doc["spec"] if doc["kind"] == "Pod" else doc["spec"]["template"]["spec"]
        for container in spec.get("initContainers", []) + spec.get("containers", []):
            image = container["image"]
            if ":" not in image.rsplit("/", 1)[-1] or image.endswith(":latest"):
                raise SystemExit("Unpinned image: " + image)
            images.add(image)
if len([d for d in docs if d["kind"] in ("Deployment", "StatefulSet")]) != 5:
    raise SystemExit("Release must render all five core workloads")
(out / "images.txt").write_text("\n".join(sorted(images)) + "\n")
subprocess.run(["helm", "package", str(CHART), "--destination", str(out)], check=True)
for filename in ("README.md", "Chart.lock"):
    shutil.copy2(CHART / filename, out / filename)
shutil.copytree(CHART / "examples", out / "examples")
(out / "tests").mkdir()
for filename in ("check_render.py", "smoke.py", "check_grafana.py", "verify_images.py"):
    shutil.copy2(CHART / "tests" / filename, out / "tests" / filename)
manifest = {"chart": "tracing-stack", "version": yaml.safe_load((CHART / "Chart.yaml").read_text())["version"],
            "mode": "offline" if args.offline else "online", "platform": args.platform,
            "images": []}
if args.offline:
    for image in sorted(images):
        subprocess.run(["docker", "pull", "--platform", args.platform, image], check=True)
        detail = json.loads(subprocess.check_output(["docker", "image", "inspect", image], text=True))[0]
        actual = detail["Os"] + "/" + detail["Architecture"]
        if actual != args.platform:
            raise SystemExit(f"Wrong platform for {image}: {actual}")
        manifest["images"].append({"reference": image, "id": detail["Id"], "repoDigests": detail["RepoDigests"]})
    subprocess.run(["docker", "save", "-o", str(out / "images.tar"), *sorted(images)], check=True)
else:
    manifest["images"] = [{"reference": image} for image in sorted(images)]
(out / "release-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
with (out / "SHA256SUMS").open("w") as output:
    for file in sorted(out.rglob("*")):
        if file.is_file() and file.name != "SHA256SUMS":
            digest = hashlib.sha256()
            with file.open("rb") as stream:
                for block in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(block)
            output.write(f"{digest.hexdigest()}  {file.relative_to(out)}\n")
print(f"Created {manifest['mode']} distribution: {out}")
