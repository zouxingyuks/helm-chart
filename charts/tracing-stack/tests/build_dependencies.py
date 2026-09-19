"""Build locked dependencies using isolated Helm repo configuration/cache."""
import pathlib
import subprocess
import tempfile
import yaml

CHART = pathlib.Path(__file__).resolve().parents[1]


def build():
    lock = yaml.safe_load((CHART / "Chart.lock").read_text())
    with tempfile.TemporaryDirectory(prefix="tracing-helm-repos-") as directory:
        root = pathlib.Path(directory)
        flags = ["--repository-config", str(root / "repositories.yaml"),
                 "--repository-cache", str(root / "cache")]
        for index, url in enumerate(sorted({d["repository"] for d in lock["dependencies"]})):
            if url.startswith("file://"):
                continue
            subprocess.run(["helm", "repo", "add", f"tracing-{index}", url, *flags], check=True)
        subprocess.run(["helm", "dependency", "build", str(CHART), "--skip-refresh", *flags], check=True)


if __name__ == "__main__":
    build()
