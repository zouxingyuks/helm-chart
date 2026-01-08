# Subconverter Helm Chart

## Introduction

Subconverter is a utility to convert between various proxy subscription formats. It supports conversion between Clash, V2Ray, Surge, Quantumult X, and many other popular proxy clients.

This Helm chart deploys a complete subconverter instance on Kubernetes with flexible configuration options.

## Prerequisites

- Kubernetes 1.20+
- Helm 3.0+

## Installation

### Install from local chart

```bash
helm install subconverter charts/subconverter
```

### Install with custom values

```bash
helm install subconverter charts/subconverter -f custom-values.yaml
```

## Configuration

The following table lists the configurable parameters of the subconverter chart:

### General Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `image.repository` | Container image repository | `tindy2013/subconverter` |
| `image.tag` | Container image tag | `0.9.0` |
| `image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `replicaCount` | Number of replicas | `1` |

### Service Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `service.type` | Kubernetes service type | `ClusterIP` |
| `service.port` | Service port | `25500` |
| `service.annotations` | Service annotations | `{}` |

### Ingress Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress | `false` |
| `ingress.className` | Ingress class name | `nginx` |
| `ingress.hostname` | Ingress hostname | `subconverter.example.com` |
| `ingress.tls` | Ingress TLS configuration | `[]` |

### Configuration Mode

| Parameter | Description | Default |
|-----------|-------------|---------|
| `configMode` | Configuration mode (default/configmap/customImage) | `default` |
| `configFiles` | Configuration files for configmap mode | `{}` |

### Resources

| Parameter | Description | Default |
|-----------|-------------|---------|
| `resources.limits.cpu` | CPU limit | `500m` |
| `resources.limits.memory` | Memory limit | `512Mi` |
| `resources.requests.cpu` | CPU request | `100m` |
| `resources.requests.memory` | Memory request | `128Mi` |

## Usage Examples

### Basic Deployment

```bash
helm install subconverter charts/subconverter
```

### Custom Configuration with ConfigMap

```yaml
configMode: configmap
configFiles:
  pref.yaml: |
    # Your pref configuration
```

### Custom Image with Embedded Configuration

```yaml
image:
  repository: myregistry/subconverter-custom
  tag: v1.0.0
configMode: customImage
```

### Ingress with TLS

```yaml
ingress:
  enabled: true
  hostname: subconverter.example.com
  tls:
    - hosts:
        - subconverter.example.com
      secretName: subconverter-tls
```

## Upgrading

```bash
helm upgrade subconverter charts/subconverter
```

## Uninstalling

```bash
helm uninstall subconverter
```

## Troubleshooting

### Check pod status

```bash
kubectl get pods -l app.kubernetes.io/name=subconverter
```

### View logs

```bash
kubectl logs -l app.kubernetes.io/name=subconverter
```

### Test health endpoint

```bash
kubectl exec -it <pod-name> -- curl http://localhost:25500/version
```

## References

- [Subconverter GitHub](https://github.com/tindy2013/subconverter)
- [Subconverter Documentation](https://github.com/tindy2013/subconverter/blob/master/README-docker.md)
