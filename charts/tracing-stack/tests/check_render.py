"""Run with /usr/bin/python3; requires PyYAML and locally built Helm dependencies."""
import pathlib
import subprocess
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHART = ROOT if (ROOT / "Chart.yaml").exists() else next(ROOT.glob("tracing-stack-*.tgz"))


def render(release, *args):
    return list(filter(None, yaml.safe_load_all(subprocess.check_output([
        "helm", "template", release, str(CHART), "-n", "observability", *args
    ], text=True))))


def config(docs, key):
    return next(yaml.safe_load(d["data"][key]) for d in docs
                if d["kind"] == "ConfigMap" and key in d.get("data", {}))


EXTERNAL = [
    "--set", "global.grafana.install=false",
    "--set", "global.prometheus.install=false",
    "--set", "global.prometheus.url=http://prometheus.example:9090",
    "--set", "global.loki.install=false",
    "--set", "global.loki.url=http://loki.example:3100",
]


for release in ("tracing", "tempo", "my-loki", "gateway", "prometheus", "x" * 53):
    for bundled in (False, True):
        docs = render(release, *([] if bundled else EXTERNAL))
        services = {d["metadata"]["name"] for d in docs if d["kind"] == "Service"}
        datasource_cm = next(d for d in docs if d["kind"] == "ConfigMap"
                             and d["metadata"]["name"] == f"{release}-tracing-datasources")
        labels = datasource_cm["metadata"]["labels"]
        assert labels["app.kubernetes.io/name"] == "tracing-stack"
        assert labels["app.kubernetes.io/instance"] == release
        assert labels["app.kubernetes.io/managed-by"] == "Helm"
        assert labels["tracing_stack_datasource" if bundled else "grafana_datasource"] == (release if bundled else "1")
        relay = config(docs, "relay")
        pipelines = relay["service"]["pipelines"]
        assert set(pipelines) == {"logs", "metrics", "traces"}
        assert set(relay["receivers"]) == {"otlp"}
        assert "debug" not in relay["exporters"]
        for pipeline in pipelines.values():
            assert pipeline["processors"] == ["memory_limiter", "batch"]
            assert all(e in relay["exporters"] for e in pipeline["exporters"])
        tempo_host = relay["exporters"]["otlp/tempo"]["endpoint"].split(":")[0]
        assert tempo_host in services, (release, tempo_host, services)
        loki_url = relay["exporters"]["otlphttp/loki"]["endpoint"]
        assert loki_url.endswith("/otlp") and "/v1/logs" not in loki_url
        if bundled:
            assert loki_url.split("//")[1].split(":")[0] in services
            loki = config(docs, "config.yaml")
            assert loki["limits_config"]["allow_structured_metadata"]
            assert loki["schema_config"]["configs"][0]["schema"] == "v13"
        else:
            assert loki_url == "http://loki.example:3100/otlp"
            assert not any("loki" in d["metadata"].get("labels", {}).get(
                "app.kubernetes.io/name", "") for d in docs)
        tempo = config(docs, "tempo.yaml")
        assert set(tempo["overrides"]["defaults"]["metrics_generator"]["processors"]) == {
            "service-graphs", "span-metrics", "local-blocks"}
        remote = tempo["metrics_generator"]["storage"]["remote_write"][0]
        assert remote["send_exemplars"]
        assert remote["url"] == relay["exporters"]["prometheusremotewrite"]["endpoint"]
        sources = config(docs, f"{release}-tracing-datasources.yaml")["datasources"]
        trace_ds = next(s for s in sources if s["type"] == "tempo")
        log_ds = next(s for s in sources if s["type"] == "loki")
        if bundled:
            prom_ds = next(s for s in sources if s["type"] == "prometheus")
            assert prom_ds["jsonData"]["exemplarTraceIdDestinations"][0]["datasourceUid"] == trace_ds["uid"]
            assert prom_ds["url"].split("//")[1].split(":")[0] in services
            assert remote["url"] == prom_ds["url"] + "/api/v1/write"
        else:
            assert len(sources) == 2
        assert trace_ds["url"].split("//")[1].split(".")[0] == tempo_host
        assert log_ds["jsonData"]["derivedFields"][0]["datasourceUid"] == trace_ds["uid"]
        assert trace_ds["jsonData"]["tracesToLogsV2"]["datasourceUid"] == log_ds["uid"]
        assert "$${__span.traceId}" in trace_ds["jsonData"]["tracesToLogsV2"]["query"]
        workloads = [d for d in docs if d["kind"] in ("Deployment", "StatefulSet")]
        assert len(workloads) == (5 if bundled else 2)
        assert all(d["spec"]["replicas"] == 1 for d in workloads)
        for d in workloads:
            assert d["spec"].get("persistentVolumeClaimRetentionPolicy", {}).get(
                "whenDeleted", "Retain") == "Retain"

docs = render("custom", *EXTERNAL, "--set", "global.prometheus.url=http://metrics.example:9090/",
              "--set", "global.loki.url=http://logs.example:3100/",
              "--set", "grafanaDatasources.enabled=false")
assert config(docs, "relay")["exporters"]["prometheusremotewrite"]["endpoint"] == \
    "http://metrics.example:9090/api/v1/write"
assert config(docs, "relay")["exporters"]["otlphttp/loki"]["endpoint"] == \
    "http://logs.example:3100/otlp"
for setting in ("tempo.fullnameOverride=broken", "tempo.replicas=2", "loki.nameOverride=broken", "global.prometheus.install=false",
                "global.loki.install=false", "grafanaDatasources.enabled=false",
                "prometheus.server.fullnameOverride=broken"):
    result = subprocess.run(["helm", "template", "invalid", str(CHART), "--set", setting],
                            capture_output=True, text=True)
    assert result.returncode != 0, setting
print("PASS: 13 render scenarios, all signal pipelines, service names, correlation, PVC retention, and invalid overrides")
