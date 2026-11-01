"""Check library integration; requires Helm and PyYAML, never accesses a cluster."""

import argparse
import pathlib
import subprocess
import tarfile
import tempfile

import yaml

CHART = pathlib.Path(__file__).resolve().parents[1]


def run(*args, values=None):
    result = subprocess.run(
        list(map(str, args)),
        input=yaml.safe_dump(values or {}),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    return result.stdout


def render(chart, values, release="demo"):
    return list(
        filter(
            None,
            yaml.safe_load_all(
                run(
                    "helm",
                    "template",
                    release,
                    chart,
                    "-n",
                    "subconverter",
                    "-f",
                    "-",
                    values=values,
                )
            ),
        )
    )


def check(docs, values):
    backend = values.get("backend", {})
    frontend = values.get("frontend", {})
    fullname = values.get("fullnameOverride") or "demo-" + values.get(
        "nameOverride", "subconverter"
    )
    fullname = fullname[:63].removesuffix("-")
    name = values.get("nameOverride", "subconverter")[:63].removesuffix("-")
    sa = values.get("serviceAccount", {})
    account = sa.get("name") or (fullname if sa.get("create", True) else "default")
    for component, config in (("backend", backend), ("frontend", frontend)):
        objects = [
            d
            for d in docs
            if d["metadata"].get("labels", {}).get("app.kubernetes.io/component")
            == component
        ]
        if not config.get("enabled", True):
            assert not objects
            continue
        selector = {
            "app.kubernetes.io/name": name,
            "app.kubernetes.io/instance": "demo",
            "app.kubernetes.io/component": component,
        }
        deployment = next(d for d in objects if d["kind"] == "Deployment")
        service = next(d for d in objects if d["kind"] == "Service")
        expected = (fullname + "-" + component)[:63].removesuffix("-")
        assert deployment["metadata"]["name"] == service["metadata"]["name"] == expected
        assert deployment["spec"]["selector"]["matchLabels"] == selector
        assert deployment["spec"]["template"]["metadata"]["labels"] == selector
        assert service["spec"]["selector"] == selector
        pod = deployment["spec"]["template"]["spec"]
        assert pod["serviceAccountName"] == account
        if config.get("image", {}).get("pullSecrets"):
            assert pod["imagePullSecrets"] == config["image"]["pullSecrets"]
        if component == "backend":
            image = config.get("image", {})
            assert pod["containers"][0]["image"] == (
                image.get("repository", "asdlokj1qpi23/subconverter")
                + ":"
                + (image.get("tag") or "0.9.0")
            )
            persistence = config.get("persistence", {})
            if persistence.get("enabled"):
                claim_name = persistence.get("existingClaim") or fullname + "-config"
                assert (
                    pod["volumes"][0]["persistentVolumeClaim"]["claimName"]
                    == claim_name
                )
                claims = [d for d in docs if d["kind"] == "PersistentVolumeClaim"]
                if persistence.get("existingClaim"):
                    assert not claims
                else:
                    assert len(claims) == 1
                    assert claims[0]["metadata"]["name"] == claim_name
                    storage = persistence.get("storageClass", "")
                    if storage:
                        assert claims[0]["spec"]["storageClassName"] == (
                            "" if storage == "-" else storage
                        )
                    else:
                        assert "storageClassName" not in claims[0]["spec"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline", type=pathlib.Path, help="Pre-migration chart snapshot"
    )
    args = parser.parse_args()
    cases = [
        {},
        {"nameOverride": "alternate"},
        {"nameOverride": "b" * 80},
        {"fullnameOverride": "fixed"},
        {"fullnameOverride": "a" * 62 + "-tail"},
        {"fullnameOverride": "a" * 80, "backend": {"persistence": {"enabled": True}}},
        {"serviceAccount": {"create": False}},
        {"serviceAccount": {"create": False, "name": "existing"}},
        {"serviceAccount": {"name": "custom"}},
        {"backend": {"image": {"repository": "example/backend", "tag": ""}}},
        {
            "backend": {
                "image": {
                    "tag": "custom",
                    "pullSecrets": [{"name": "key"}, {"name": "key"}],
                }
            }
        },
        {
            "frontend": {
                "image": {"tag": "custom", "pullSecrets": [{"name": "frontend-key"}]}
            }
        },
        {"backend": {"persistence": {"enabled": True, "existingClaim": "retained"}}},
        {"ingress": {"enabled": True}},
        {"frontend": {"enabled": False}, "ingress": {"enabled": True}},
        {
            "ingress": {
                "enabled": True,
                "hosts": [
                    {
                        "name": "web.example.com",
                        "serviceName": "demo-subconverter-frontend",
                        "servicePort": 80,
                    },
                    {
                        "name": "api.example.com",
                        "serviceName": "demo-subconverter-backend",
                        "servicePort": 25500,
                    },
                ],
            }
        },
        {"backend": {"configMode": "configmap", "configFiles": {"pref.ini": "test"}}},
    ]
    cases += [
        {"backend": {"persistence": {"enabled": True, "storageClass": storage}}}
        for storage in ("", "-", "fast")
    ]
    cases += [
        {
            "backend": {
                "enabled": backend,
                "autoscaling": {"enabled": True},
                "podDisruptionBudget": {"enabled": True},
            },
            "frontend": {
                "enabled": frontend,
                "autoscaling": {"enabled": True},
                "podDisruptionBudget": {"enabled": True},
            },
        }
        for backend in (False, True)
        for frontend in (False, True)
    ]
    with tempfile.TemporaryDirectory(prefix="subconverter-migration-") as tmp:
        run("helm", "lint", CHART, "--strict")
        run("helm", "package", CHART, "--destination", tmp)
        package = next(pathlib.Path(tmp).glob("subconverter-*.tgz"))
        with tarfile.open(package) as archive:
            members = archive.getnames()
            for filename in ("Chart.yaml", "README.md", "LICENSE", "NOTICE"):
                assert f"subconverter/charts/homelab-common/{filename}" in members
        for values in cases:
            docs = render(CHART, values)
            check(docs, values)
            assert render(package, values) == docs, values
            if args.baseline:
                assert render(args.baseline, values) == docs, values
        for release in ("subconverter", "my-subconverter", "x" * 53):
            docs = render(CHART, {}, release)
            assert render(package, {}, release) == docs
            if args.baseline:
                assert render(args.baseline, {}, release) == docs
    print(
        f"PASS: {len(cases)} value scenarios, release names, strict lint, and packaged chart"
        + ("; all manifests equal baseline" if args.baseline else "")
    )


if __name__ == "__main__":
    main()
