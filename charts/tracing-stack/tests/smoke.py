"""Verify OTLP signals, Tempo span metrics, service graph and exemplars. Python stdlib only."""
import argparse
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request


def request(url, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.load(response)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name, port in (("gateway", 14318), ("tempo", 13200), ("loki", 13100), ("prometheus", 19090)):
        parser.add_argument(f"--{name}", default=f"http://127.0.0.1:{port}")
    args = parser.parse_args()
    trace_id, span_id = secrets.token_hex(16), secrets.token_hex(8)
    timestamp = time.time_ns()
    resource = {"attributes": [{"key": "service.name", "value": {"stringValue": "tracing-smoke"}}]}
    span = {"traceId": trace_id, "spanId": span_id, "name": "smoke", "kind": 2,
            "startTimeUnixNano": str(timestamp), "endTimeUnixNano": str(timestamp + 1000000),
            "status": {"code": 1}}
    client_id = secrets.token_hex(8)
    client = dict(span, spanId=client_id, parentSpanId=span_id, name="call-backend", kind=3)
    backend = dict(span, spanId=secrets.token_hex(8), parentSpanId=client_id, name="backend", kind=2)
    backend_resource = {"attributes": [{"key": "service.name", "value": {"stringValue": "tracing-smoke-backend"}}]}
    trace = {"resourceSpans": [
        {"resource": resource, "scopeSpans": [{"spans": [span, client]}]},
        {"resource": backend_resource, "scopeSpans": [{"spans": [backend]}]},
    ]}
    log = {"timeUnixNano": str(timestamp), "observedTimeUnixNano": str(timestamp),
           "severityNumber": 9, "severityText": "INFO", "traceId": trace_id, "spanId": span_id,
           "body": {"stringValue": f"tracing smoke {trace_id}"}}
    logs = {"resourceLogs": [{"resource": resource, "scopeLogs": [{"logRecords": [log]}]}]}
    metric = {"name": "tracing_stack_smoke", "gauge": {"dataPoints": [{
        "timeUnixNano": str(timestamp), "asDouble": 1,
        "attributes": [{"key": "test_run", "value": {"stringValue": trace_id}}]}]}}
    metrics = {"resourceMetrics": [{"resource": resource, "scopeMetrics": [{"metrics": [metric]}]}]}
    for signal, payload in (("traces", trace), ("logs", logs), ("metrics", metrics)):
        response = request(args.gateway.rstrip("/") + "/v1/" + signal, payload)
        if response.get("partialSuccess"):
            raise RuntimeError(f"{signal}: partial success: {response}")
    print(f"Accepted all signals; trace ID: {trace_id}", flush=True)
    log_query = urllib.parse.urlencode({"query": '{service_name="tracing-smoke"} | trace_id = "' + trace_id + '"'})
    metric_query = urllib.parse.urlencode({"query": 'tracing_stack_smoke{test_run="' + trace_id + '"}'})
    checks = {
        "trace": (args.tempo.rstrip("/") + "/api/traces/" + trace_id,
                  lambda d: bool(d.get("batches") or d.get("resourceSpans"))),
        "log": (args.loki.rstrip("/") + "/loki/api/v1/query_range?" + log_query,
                lambda d: bool(d.get("data", {}).get("result"))),
        "metric": (args.prometheus.rstrip("/") + "/api/v1/query?" + metric_query,
                   lambda d: bool(d.get("data", {}).get("result"))),
    }
    for label, query in {
        "span metrics": 'traces_spanmetrics_calls_total{service="tracing-smoke"}',
        "service graph": 'traces_service_graph_request_total{client="tracing-smoke",server="tracing-smoke-backend"}',
    }.items():
        checks[label] = (args.prometheus.rstrip("/") + "/api/v1/query?" + urllib.parse.urlencode({"query": query}),
                         lambda d: bool(d.get("data", {}).get("result")))
    exemplar_query = urllib.parse.urlencode({"query": 'traces_spanmetrics_latency_bucket{service="tracing-smoke"}',
                                             "start": str(timestamp / 1e9 - 5), "end": str(timestamp / 1e9 + 180)})
    checks["exemplar"] = (
        args.prometheus.rstrip("/") + "/api/v1/query_exemplars?" + exemplar_query,
        lambda d: any(e.get("labels", {}).get("traceID") == trace_id
                      for series in d.get("data", []) for e in series.get("exemplars", [])),
    )
    deadline = time.monotonic() + 120
    errors = {}
    while checks and time.monotonic() < deadline:
        for signal, (url, valid) in list(checks.items()):
            try:
                if valid(request(url)):
                    del checks[signal]
                    print(f"PASS {signal}", flush=True)
            except (urllib.error.URLError, TimeoutError, ValueError) as error:
                errors[signal] = str(error)
        if checks:
            time.sleep(3)
    if checks:
        raise SystemExit(f"Failed to query {list(checks)}; last errors: {errors}")


if __name__ == "__main__":
    main()
