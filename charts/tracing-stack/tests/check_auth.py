"""Validate OTLP HTTP bearer authentication using synthetic credentials. Requires Docker and PyYAML."""

import http.server, json, pathlib, subprocess, threading, time, urllib.request, urllib.error, yaml, tempfile

root = pathlib.Path(tempfile.mkdtemp(prefix="tracing-auth-"))
chart_root = pathlib.Path(__file__).resolve().parents[1]
chart = (
    chart_root
    if (chart_root / "Chart.yaml").exists()
    else next(chart_root.glob("tracing-stack-*.tgz"))
)
docs = list(
    filter(
        None,
        yaml.safe_load_all(
            subprocess.check_output(
                [
                    "helm",
                    "template",
                    "tracing",
                    str(chart),
                    "-n",
                    "observability",
                    "-f",
                    str(chart_root / "examples" / "otlp-ingress.yaml"),
                ],
                text=True,
            )
        ),
    )
)
c = next(
    yaml.safe_load(d["data"]["relay"])
    for d in docs
    if d["kind"] == "ConfigMap" and d["metadata"]["name"] == "tracing-otlp-edge"
)
c["receivers"]["otlp"]["protocols"]["http"]["endpoint"] = "127.0.0.1:24318"
c["receivers"]["otlp"]["protocols"]["grpc"]["endpoint"] = "127.0.0.1:24317"
c["extensions"]["health_check"]["endpoint"] = "127.0.0.1:24333"
c["exporters"]["otlphttp"]["endpoint"] = "http://127.0.0.1:24322"
(root / "config.yaml").write_text(yaml.safe_dump(c))
received = []


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        received.append(self.rfile.read(int(self.headers["Content-Length"])))
        self.send_response(200)
        self.send_header("Content-Type", "application/x-protobuf")
        self.end_headers()

    def log_message(self, *args):
        pass


server = http.server.ThreadingHTTPServer(("127.0.0.1", 24322), Handler)
threading.Thread(target=server.serve_forever, daemon=True).start()
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
name = root.name
try:
    subprocess.run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "--network",
            "host",
            "-e",
            "OTLP_TOKEN=synthetic-test-token",
            "--mount",
            f"type=bind,source={root}/config.yaml,target=/etc/otelcol/config.yaml,readonly",
            "ghcr.io/open-telemetry/opentelemetry-collector-releases/opentelemetry-collector-contrib:0.145.0",
            "--config=/etc/otelcol/config.yaml",
        ],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    for _ in range(40):
        try:
            opener.open("http://127.0.0.1:24333", timeout=1)
            break
        except Exception:
            time.sleep(0.25)
    data = json.dumps(
        {
            "resourceLogs": [
                {
                    "scopeLogs": [
                        {"logRecords": [{"body": {"stringValue": "auth-test"}}]}
                    ]
                }
            ]
        }
    ).encode()
    for token, expected in [
        (None, 401),
        ("invalid", 401),
        ("synthetic-test-token", 200),
    ]:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        req = urllib.request.Request(
            "http://127.0.0.1:24318/v1/logs", data=data, headers=headers
        )
        try:
            code = opener.open(req, timeout=10).status
        except urllib.error.HTTPError as e:
            code = e.code
        assert code == expected, (token is not None, code, expected)
    assert len(received) == 1, len(received)
    print(
        "PASS: missing/invalid bearer token rejected, valid token forwarded exactly once"
    )
finally:
    subprocess.run(["docker", "rm", "-f", name], stdout=subprocess.DEVNULL)
    server.shutdown()
    server.server_close()
