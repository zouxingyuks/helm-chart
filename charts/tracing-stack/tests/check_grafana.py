"""Verify provisioning, health, and cross-signal links in a running Grafana."""
import argparse
import base64
import json
import pathlib
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--url", default="http://127.0.0.1:13000")
parser.add_argument("--user", default="admin")
parser.add_argument("--password-file", required=True, type=pathlib.Path)
args = parser.parse_args()
auth = base64.b64encode(f"{args.user}:{args.password_file.read_text().strip()}".encode()).decode()


def get(path):
    req = urllib.request.Request(args.url.rstrip("/") + path,
                                 headers={"Authorization": "Basic " + auth})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.load(response)


sources = {}
for uid in ("prometheus", "tracing-tempo", "tracing-loki"):
    sources[uid] = get("/api/datasources/uid/" + uid)
    health = get("/api/datasources/uid/" + uid + "/health")
    assert health["status"] == "OK", (uid, health)
    print("PASS datasource health:", uid)
t = sources["tracing-tempo"]["jsonData"]
l = sources["tracing-loki"]["jsonData"]
p = sources["prometheus"]["jsonData"]
assert t["serviceMap"]["datasourceUid"] == "prometheus"
assert t["tracesToMetrics"]["datasourceUid"] == "prometheus"
assert t["tracesToLogsV2"]["datasourceUid"] == "tracing-loki"
assert "${__span.traceId}" in t["tracesToLogsV2"]["query"]
assert "$${" not in t["tracesToLogsV2"]["query"]
assert l["derivedFields"][0]["datasourceUid"] == "tracing-tempo"
assert l["derivedFields"][0]["url"] == "${__value.raw}"
assert p["exemplarTraceIdDestinations"][0]["datasourceUid"] == "tracing-tempo"
print("PASS provisioned service-map, metrics, logs, and exemplar links")
