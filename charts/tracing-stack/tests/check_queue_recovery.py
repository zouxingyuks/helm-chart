"""Verify Alloy persistent queue replay after backend failure and SIGKILL. Requires Docker and PyYAML."""

import gzip, json, pathlib, subprocess, tempfile, threading, time, urllib.request, http.server
import yaml

root = pathlib.Path(tempfile.mkdtemp(prefix="tracing-alloy-durability-"))
(root / "queue").mkdir()
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
                ["helm", "template", "tracing", str(chart), "-n", "observability"],
                text=True,
            )
        ),
    )
)
source = next(
    d["data"]["config.alloy"]
    for d in docs
    if d["kind"] == "ConfigMap" and "config.alloy" in d.get("data", {})
)
alloy_image = next(
    c["image"]
    for d in docs
    if d["kind"] == "StatefulSet"
    for c in d["spec"]["template"]["spec"]["containers"]
    if c["name"] == "alloy"
)
config = (
    source[source.index('otelcol.storage.file "queue"') :]
    .replace("/var/lib/alloy/queue", "/data/queue")
    .replace("http://tracing-gateway:4318", "http://127.0.0.1:24320")
)
config += """\notelcol.receiver.otlp "test" {
  http { endpoint = "127.0.0.1:24319" }
  output { logs = [otelcol.exporter.otlphttp.gateway.input] }
}\n"""
(root / "config.alloy").write_text(config)
name = root.name
cmd = [
    "docker",
    "run",
    "-d",
    "--name",
    name,
    "--network",
    "host",
    "--mount",
    f"type=bind,source={root},target=/data",
    alloy_image,
    "run",
    "--stability.level=public-preview",
    "--server.http.listen-addr=127.0.0.1:24321",
    "--storage.path=/data/state",
    "/data/config.alloy",
]
received = []


class Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers["Content-Length"]))
        if self.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        received.append(data)
        self.send_response(200)
        self.send_header("Content-Type", "application/x-protobuf")
        self.end_headers()

    def log_message(self, *args):
        pass


opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def wait_ready():
    for _ in range(40):
        try:
            opener.open("http://127.0.0.1:24321/-/ready", timeout=1)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError("Alloy did not become ready")


def cleanup():
    subprocess.run(
        ["docker", "rm", "-f", name],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


server = None
try:
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    wait_ready()
    marker = "durability-check-0123456789"
    payload = {
        "resourceLogs": [
            {"scopeLogs": [{"logRecords": [{"body": {"stringValue": marker}}]}]}
        ]
    }
    req = urllib.request.Request(
        "http://127.0.0.1:24319/v1/logs",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    response = opener.open(req, timeout=10).read()
    assert (
        not json.loads(response).get("partialSuccess", {}).get("rejectedLogRecords")
    ), response
    time.sleep(2)
    assert any((root / "queue").rglob("*")), "No queue files"
    subprocess.run(
        ["docker", "kill", "--signal", "KILL", name],
        check=True,
        stdout=subprocess.DEVNULL,
    )
    subprocess.run(["docker", "rm", name], check=True, stdout=subprocess.DEVNULL)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 24320), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
    wait_ready()
    for _ in range(60):
        if any(marker.encode() in x for x in received):
            break
        time.sleep(0.5)
    assert any(marker.encode() in x for x in received), (
        "Queued record was not recovered"
    )
    print(
        "PASS: backend unavailable, record accepted, SIGKILL, persistent queue replay after restart"
    )
finally:
    if server:
        server.shutdown()
        server.server_close()
    cleanup()
    print("Evidence directory:", root)
