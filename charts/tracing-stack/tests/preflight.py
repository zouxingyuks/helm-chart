"""Check existing Prometheus Operator ownership before installing tracing-stack.

Read-only. Run with a kubeconfig/context already selected by the operator.
"""

import argparse
import json
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--namespace", required=True)
parser.add_argument("--release", required=True)
parser.add_argument("--reuse-operator", action="store_true")
args = parser.parse_args()
command = [
    "kubectl",
    "get",
    "deployment",
    "--all-namespaces",
    "-l",
    "app.kubernetes.io/component=prometheus-operator",
    "-o",
    "json",
]
items = json.loads(subprocess.check_output(command, text=True))["items"]
foreign = [
    d
    for d in items
    if not (
        d["metadata"]["namespace"] == args.namespace
        and d["metadata"].get("labels", {}).get("app.kubernetes.io/instance")
        == args.release
    )
]
if foreign and not args.reuse_operator:
    names = [d["metadata"]["namespace"] + "/" + d["metadata"]["name"] for d in foreign]
    raise SystemExit(
        "Existing Operator detected: "
        + ", ".join(names)
        + ". Configure examples/existing-operator.yaml or remove the old installation explicitly."
    )
if args.reuse_operator and not foreign:
    raise SystemExit(
        "No existing Operator with the standard component label was found; verify ownership manually."
    )
if args.reuse_operator:
    print(
        "Existing Operator found. Verify its namespace and instance selectors admit the new Prometheus/Alertmanager CRs."
    )
else:
    print("No foreign Operator with the standard component label found.")
print(
    "This check cannot detect custom/unlabelled Operators; verify those separately before installation."
)
