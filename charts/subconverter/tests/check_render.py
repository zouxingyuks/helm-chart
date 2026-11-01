"""Run with /usr/bin/python3; requires PyYAML and locally built Helm dependencies."""

import pathlib
import subprocess
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
CHART = (
    ROOT if (ROOT / "Chart.yaml").exists() else next(ROOT.glob("subconverter-*.tgz"))
)


def render(values=None, release="demo", error=None):
    result = subprocess.run(
        ["helm", "template", release, str(CHART), "-n", "subconverter", "-f", "-"],
        input=yaml.safe_dump(values or {}),
        capture_output=True,
        text=True,
    )
    if error is not None:
        assert result.returncode != 0, values
        assert error in result.stderr, result.stderr
        return
    assert result.returncode == 0, result.stdout + result.stderr
    return list(filter(None, yaml.safe_load_all(result.stdout)))


def resource(docs, kind, component):
    matches = [
        d
        for d in docs
        if d["kind"] == kind
        and d["metadata"].get("labels", {}).get("app.kubernetes.io/component")
        == component
    ]
    assert len(matches) == 1, (kind, component, matches)
    return matches[0]


def pod(docs, component):
    return resource(docs, "Deployment", component)["spec"]["template"]["spec"]


def check_identity(docs, release, fullname, name="subconverter"):
    for component in ("backend", "frontend"):
        expected_name = (fullname + "-" + component)[:63].rstrip("-")
        selector = {
            "app.kubernetes.io/name": name,
            "app.kubernetes.io/instance": release,
            "app.kubernetes.io/component": component,
        }
        deployment = resource(docs, "Deployment", component)
        service = resource(docs, "Service", component)
        assert deployment["metadata"]["name"] == expected_name
        assert service["metadata"]["name"] == expected_name
        assert deployment["spec"]["selector"]["matchLabels"] == selector
        assert deployment["spec"]["template"]["metadata"]["labels"] == selector
        assert service["spec"]["selector"] == selector
        for obj in (deployment, service):
            labels = obj["metadata"]["labels"]
            assert all(labels[key] == value for key, value in selector.items())
            assert labels["app.kubernetes.io/managed-by"] == "Helm"
            assert labels["helm.sh/chart"].startswith("subconverter-")
            assert labels["app.kubernetes.io/version"] == "0.9.0"
        assert pod(docs, component)["serviceAccountName"] == fullname
    accounts = [d for d in docs if d["kind"] == "ServiceAccount"]
    assert len(accounts) == 1
    assert accounts[0]["metadata"]["name"] == fullname
    assert accounts[0]["metadata"]["labels"]["app.kubernetes.io/name"] == name
    frontend_env = pod(docs, "frontend")["containers"][0]["env"]
    assert frontend_env[0] == {
        "name": "VUE_APP_SUBCONVERTER_DEFAULT_BACKEND",
        "value": "http://" + (fullname + "-backend")[:63].rstrip("-") + ":25500",
    }


for values, release, fullname, name in [
    ({}, "demo", "demo-subconverter", "subconverter"),
    ({}, "subconverter", "subconverter", "subconverter"),
    ({}, "my-subconverter", "my-subconverter", "subconverter"),
    ({}, "x" * 53, "x" * 53 + "-subconver", "subconverter"),
    ({"nameOverride": "alternate"}, "demo", "demo-alternate", "alternate"),
    ({"nameOverride": "demo"}, "demo", "demo", "demo"),
    ({"fullnameOverride": "fixed"}, "demo", "fixed", "subconverter"),
    ({"fullnameOverride": "a" * 80}, "demo", "a" * 63, "subconverter"),
    ({"fullnameOverride": "a" * 62 + "-tail"}, "demo", "a" * 62, "subconverter"),
    ({"nameOverride": "b" * 80}, "demo", "demo-" + "b" * 58, "b" * 63),
]:
    check_identity(render(values, release), release, fullname, name)


docs = render()
assert {d["kind"] for d in docs} == {"ServiceAccount", "Service", "Deployment"}
assert len(docs) == 5
backend = pod(docs, "backend")["containers"][0]
frontend = pod(docs, "frontend")["containers"][0]
assert backend["image"] == "asdlokj1qpi23/subconverter:0.9.0"
assert frontend["image"] == "careywong/subweb:latest"
assert backend["imagePullPolicy"] == frontend["imagePullPolicy"] == "IfNotPresent"
assert "env" not in backend
assert len(frontend["env"]) == 10
assert {e["name"]: e["value"] for e in frontend["env"]} == {
    "VUE_APP_SUBCONVERTER_DEFAULT_BACKEND": "http://demo-subconverter-backend:25500",
    "VUE_APP_PROJECT": "https://github.com/CareyWang/sub-web",
    "VUE_APP_BOT_LINK": "https://t.me/subconverter_discuss",
    "VUE_APP_USE_STORAGE": "true",
    "VUE_APP_CACHE_TTL": "86400",
    "VUE_APP_BACKEND_RELEASE": "https://github.com/tindy2013/subconverter/actions",
    "VUE_APP_SUBCONVERTER_REMOTE_CONFIG": "https://raw.githubusercontent.com/tindy2013/subconverter/master/base/config/example_external_config.ini",
    "VUE_APP_SUBCONVERTER_DOC_ADVANCED": "https://github.com/tindy2013/subconverter/blob/master/README-cn.md#%E8%BF%9B%E9%98%B6%E9%93%BE%E6%8E%A5",
    "VUE_APP_MYURLS_API": "",
    "VUE_APP_CONFIG_UPLOAD_API": "",
}
for component, port in (("backend", 25500), ("frontend", 80)):
    assert resource(docs, "Deployment", component)["spec"]["replicas"] == 1
    assert resource(docs, "Service", component)["spec"]["ports"][0]["port"] == port


extra_env = [
    {"name": "LITERAL", "value": "example"},
    {"name": "EMPTY", "value": ""},
    {"name": "NUMBER_STRING", "value": "123"},
    {"name": "BOOLEAN_STRING", "value": "false"},
    {
        "name": "SECRET",
        "valueFrom": {"secretKeyRef": {"name": "credentials", "key": "token"}},
    },
    {
        "name": "CONFIG",
        "valueFrom": {
            "configMapKeyRef": {"name": "settings", "key": "mode", "optional": True}
        },
    },
    {"name": "POD_NAME", "valueFrom": {"fieldRef": {"fieldPath": "metadata.name"}}},
]
docs = render(
    {
        "backend": {"env": extra_env},
        "frontend": {
            "env": extra_env,
            "apiURL": "https://api.example.com",
            "useStorage": False,
            "cacheTTL": 60,
            "projectUrl": "https://project.example.com",
            "botLink": "https://bot.example.com",
            "backendRelease": "https://release.example.com",
            "remoteConfig": "https://config.example.com",
            "advancedDoc": "https://docs.example.com",
            "myurlsApi": "https://short.example.com",
            "configUploadApi": "https://upload.example.com",
        },
    }
)
assert pod(docs, "backend")["containers"][0]["env"] == extra_env
frontend_env = pod(docs, "frontend")["containers"][0]["env"]
assert frontend_env[10:] == extra_env
assert {e["name"]: e["value"] for e in frontend_env[:10]} == {
    "VUE_APP_SUBCONVERTER_DEFAULT_BACKEND": "https://api.example.com",
    "VUE_APP_PROJECT": "https://project.example.com",
    "VUE_APP_BOT_LINK": "https://bot.example.com",
    "VUE_APP_USE_STORAGE": "false",
    "VUE_APP_CACHE_TTL": "60",
    "VUE_APP_BACKEND_RELEASE": "https://release.example.com",
    "VUE_APP_SUBCONVERTER_REMOTE_CONFIG": "https://config.example.com",
    "VUE_APP_SUBCONVERTER_DOC_ADVANCED": "https://docs.example.com",
    "VUE_APP_MYURLS_API": "https://short.example.com",
    "VUE_APP_CONFIG_UPLOAD_API": "https://upload.example.com",
}


for create, name, expected in (
    (False, "", "default"),
    (False, "existing", "existing"),
    (True, "custom", "custom"),
):
    docs = render({"serviceAccount": {"create": create, "name": name}})
    accounts = [d for d in docs if d["kind"] == "ServiceAccount"]
    assert [d["metadata"]["name"] for d in accounts] == ([expected] if create else [])
    for component in ("backend", "frontend"):
        assert pod(docs, component)["serviceAccountName"] == expected


for storage_class in ("", "-", "fast"):
    docs = render(
        {"backend": {"persistence": {"enabled": True, "storageClass": storage_class}}}
    )
    claim = resource(docs, "PersistentVolumeClaim", "backend")
    assert claim["metadata"]["name"] == "demo-subconverter-config"
    assert claim["spec"]["accessModes"] == ["ReadWriteOnce"]
    assert claim["spec"]["resources"]["requests"]["storage"] == "1Gi"
    if storage_class:
        assert claim["spec"]["storageClassName"] == (
            "" if storage_class == "-" else storage_class
        )
    else:
        assert "storageClassName" not in claim["spec"]
    assert pod(docs, "backend")["volumes"] == [
        {
            "name": "data",
            "persistentVolumeClaim": {"claimName": "demo-subconverter-config"},
        }
    ]
    assert pod(docs, "backend")["containers"][0]["volumeMounts"] == [
        {"name": "data", "mountPath": "/base"}
    ]

docs = render(
    {
        "fullnameOverride": "fixed",
        "backend": {"persistence": {"enabled": True, "existingClaim": "retained"}},
    }
)
assert not any(d["kind"] == "PersistentVolumeClaim" for d in docs)
assert (
    pod(docs, "backend")["volumes"][0]["persistentVolumeClaim"]["claimName"]
    == "retained"
)
docs = render(
    {"fullnameOverride": "a" * 80, "backend": {"persistence": {"enabled": True}}}
)
claim = resource(docs, "PersistentVolumeClaim", "backend")
assert claim["metadata"]["name"] == "a" * 63 + "-config"
assert (
    pod(docs, "backend")["volumes"][0]["persistentVolumeClaim"]["claimName"]
    == claim["metadata"]["name"]
)


for backend_enabled, frontend_enabled in (
    (True, True),
    (True, False),
    (False, True),
    (False, False),
):
    docs = render(
        {
            "backend": {
                "enabled": backend_enabled,
                "persistence": {"enabled": True},
                "autoscaling": {"enabled": True},
                "podDisruptionBudget": {"enabled": True},
            },
            "frontend": {
                "enabled": frontend_enabled,
                "apiURL": "https://api.example.com",
                "autoscaling": {"enabled": True},
                "podDisruptionBudget": {"enabled": True},
            },
        }
    )
    for component, enabled in (
        ("backend", backend_enabled),
        ("frontend", frontend_enabled),
    ):
        component_docs = [
            d
            for d in docs
            if d["metadata"].get("labels", {}).get("app.kubernetes.io/component")
            == component
        ]
        expected_kinds = {
            "Deployment",
            "Service",
            "HorizontalPodAutoscaler",
            "PodDisruptionBudget",
        }
        if component == "backend":
            expected_kinds.add("PersistentVolumeClaim")
        assert {d["kind"] for d in component_docs} == (
            expected_kinds if enabled else set()
        )
        if not enabled:
            continue
        deployment = resource(docs, "Deployment", component)
        assert "replicas" not in deployment["spec"]
        hpa = resource(docs, "HorizontalPodAutoscaler", component)
        assert hpa["spec"]["scaleTargetRef"] == {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "name": deployment["metadata"]["name"],
        }
        pdb = resource(docs, "PodDisruptionBudget", component)
        assert pdb["spec"]["selector"] == deployment["spec"]["selector"]
        assert pdb["spec"]["minAvailable"] == 1


for frontend_enabled, component, port in (
    (True, "frontend", 80),
    (False, "backend", 25500),
):
    docs = render(
        {"frontend": {"enabled": frontend_enabled}, "ingress": {"enabled": True}}
    )
    ingress = next(d for d in docs if d["kind"] == "Ingress")
    target = ingress["spec"]["rules"][0]["http"]["paths"][0]["backend"]["service"]
    assert target == {
        "name": resource(docs, "Service", component)["metadata"]["name"],
        "port": {"number": port},
    }

docs = render(
    {
        "fullnameOverride": "fixed",
        "ingress": {
            "enabled": True,
            "hosts": [
                {
                    "name": "web.example.com",
                    "serviceName": "fixed-frontend",
                    "servicePort": 80,
                },
                {
                    "name": "api.example.com",
                    "serviceName": "fixed-backend",
                    "servicePort": 25500,
                },
            ],
        },
    }
)
ingresses = [d for d in docs if d["kind"] == "Ingress"]
assert {d["metadata"]["name"] for d in ingresses} == {
    "fixed-web-example-com",
    "fixed-api-example-com",
}
for ingress in ingresses:
    rule = ingress["spec"]["rules"][0]
    component, port = (
        ("frontend", 80) if rule["host"] == "web.example.com" else ("backend", 25500)
    )
    assert rule["http"]["paths"][0]["backend"]["service"] == {
        "name": resource(docs, "Service", component)["metadata"]["name"],
        "port": {"number": port},
    }


render(
    {"backend": {"configMode": "configmap", "persistence": {"enabled": True}}},
    error="configMode 'configmap' and persistence.enabled cannot both be true",
)
for component in ("backend", "frontend"):
    render(
        {component: {"podDisruptionBudget": {"enabled": True, "maxUnavailable": 1}}},
        error=component
        + ".podDisruptionBudget.minAvailable and "
        + component
        + ".podDisruptionBudget.maxUnavailable are mutually exclusive",
    )

print(
    "PASS: names, selectors, component switches, images, environment variables, service accounts, PVCs, HPA/PDB, Ingress, and invalid configuration"
)
