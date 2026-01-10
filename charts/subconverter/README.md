# Subconverter Helm Chart

## Introduction

Subconverter is a utility to convert between various proxy subscription formats. It supports conversion between Clash,
V2Ray, Surge, Quantumult X, and many other popular proxy clients.

This Helm chart deploys a complete subconverter instance on Kubernetes with:

- **Backend**: Subconverter API service for subscription conversion
- **Frontend**: [sub-web-modify](https://github.com/youshandefeiyang/sub-web-modify) web UI with enhanced features
  including dark mode and hundreds of remote configurations

The frontend is enabled by default, providing an out-of-the-box experience with a beautiful web interface.

## Architecture

This chart deploys two containers in the same Pod when frontend is enabled:

1. **Backend Container** (`subconverter`): Runs the subconverter API service on port 25500
2. **Frontend Container** (`subconverter-frontend`): Runs the web UI on port 80

### Container Communication

When both containers are enabled, they communicate via `localhost` since they share the same network namespace in the
Pod:

- Frontend → Backend: `http://localhost:25500`
- This is configured automatically via the `API_URL` environment variable

For external API configuration, set `frontend.apiURL` to point to a remote backend.

## Prerequisites

- Kubernetes 1.20+
- Helm 3.0+

## Installation

### Quick Start (Default with Frontend)

```bash
helm install subconverter charts/subconverter
```

This installs both the backend and frontend containers. The frontend will be accessible via port-forwarding or Ingress.

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

| Parameter          | Description                | Default                      |
|--------------------|----------------------------|------------------------------|
| `image.repository` | Container image repository | `asdlokj1qpi23/subconverter` |
| `image.tag`        | Container image tag        | `0.9.0`                      |
| `image.pullPolicy` | Image pull policy          | `IfNotPresent`               |
| `replicaCount`     | Number of replicas         | `1`                          |

### Frontend Configuration

| Parameter                   | Description                                  | Default                           |
|-----------------------------|----------------------------------------------|-----------------------------------|
| `frontend.enabled`          | Enable frontend container                    | `true`                            |
| `frontend.image.repository` | Frontend image repository                    | `youshandefeiyang/sub-web-modify` |
| `frontend.image.tag`        | Frontend image tag                           | `latest`                          |
| `frontend.apiURL`           | External API URL (empty = use local backend) | `""`                              |
| `frontend.env`              | Additional environment variables             | `[]`                              |
| `frontend.resources`        | Frontend resource limits/requests            | See below                         |

#### Frontend Resources

| Parameter                            | Description             | Default |
|--------------------------------------|-------------------------|---------|
| `frontend.resources.limits.cpu`      | Frontend CPU limit      | `200m`  |
| `frontend.resources.limits.memory`   | Frontend memory limit   | `256Mi` |
| `frontend.resources.requests.cpu`    | Frontend CPU request    | `50m`   |
| `frontend.resources.requests.memory` | Frontend memory request | `64Mi`  |

### Service Configuration

| Parameter             | Description             | Default     |
|-----------------------|-------------------------|-------------|
| `service.type`        | Kubernetes service type | `ClusterIP` |
| `service.port`        | Backend service port    | `25500`     |
| `service.annotations` | Service annotations     | `{}`        |

#### Service Ports

When frontend is enabled, the service exposes two ports:

- **Port 80** (named `http`): Frontend web UI - Use this for accessing the web interface
- **Port 25500** (named `backend`): Backend API - Use this for direct API access

When frontend is disabled, only port 25500 is exposed.

#### Accessing the Services

```bash
# Access the frontend web UI
kubectl port-forward svc/subconverter 8080:80
# Open browser at http://localhost:8080

# Access the backend API directly
kubectl port-forward svc/subconverter 25500:25500
# Test: curl http://localhost:25500/version
```

### Ingress Configuration

| Parameter           | Description               | Default                    |
|---------------------|---------------------------|----------------------------|
| `ingress.enabled`   | Enable ingress            | `false`                    |
| `ingress.className` | Ingress class name        | `nginx`                    |
| `ingress.hostname`  | Ingress hostname          | `subconverter.example.com` |
| `ingress.tls`       | Ingress TLS configuration | `[]`                       |

#### Ingress Behavior

By default, when frontend is enabled, the Ingress routes traffic to the frontend (port 80). Users can access the web UI
through the Ingress hostname.

#### Separate Ingress for Frontend and Backend

If you need separate Ingress rules for frontend and backend:

```yaml
# Frontend Ingress (default)
ingress:
  enabled: true
  hostname: subconverter.example.com
  tls:
    - hosts:
        - subconverter.example.com
      secretName: subconverter-tls

# For backend API access, create an additional Ingress manually
# or disable frontend and use the default Ingress configuration
```

#### Backend-Only Ingress

When frontend is disabled, Ingress routes directly to the backend API:

```yaml
frontend:
  enabled: false

ingress:
  enabled: true
  hostname: subconverter-api.example.com
```

### Configuration Mode

| Parameter     | Description                                        | Default   |
|---------------|----------------------------------------------------|-----------|
| `configMode`  | Configuration mode (default/configmap/customImage) | `default` |
| `configFiles` | Configuration files for configmap mode             | `{}`      |

### Resources

| Parameter                   | Description    | Default |
|-----------------------------|----------------|---------|
| `resources.limits.cpu`      | CPU limit      | `500m`  |
| `resources.limits.memory`   | Memory limit   | `512Mi` |
| `resources.requests.cpu`    | CPU request    | `100m`  |
| `resources.requests.memory` | Memory request | `128Mi` |

## Usage Examples

### Default Deployment (Frontend + Backend)

```bash
helm install subconverter charts/subconverter
```

This deploys both frontend and backend containers. Access the web UI:

```bash
kubectl port-forward svc/subconverter 8080:80
# Open browser at http://localhost:8080
```

### Backend Only (Disable Frontend)

Use the provided values file:

```bash
helm install subconverter charts/subconverter -f charts/subconverter/values-no-frontend.yaml
```

Or set in your custom values:

```yaml
frontend:
  enabled: false
```

### Frontend with External API

For frontend-backend separation:

```bash
helm install subconverter charts/subconverter -f charts/subconverter/values-external-api.yaml
```

Custom configuration:

```yaml
frontend:
  enabled: true
  apiURL: "https://subconverter-api.example.com"
  env:
    - name: NODE_ENV
      value: production
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

### Standard Upgrade

```bash
helm upgrade subconverter charts/subconverter
```

### Upgrade from Backend-Only to Frontend+Backend

If you have an existing deployment without the frontend:

```bash
# Upgrade with frontend enabled (default)
helm upgrade subconverter charts/subconverter
```

To keep backend-only configuration:

```bash
helm upgrade subconverter charts/subconverter --set frontend.enabled=false
```

**Important**: When upgrading from chart version 0.1.0 to 0.2.0+, the frontend is enabled by default. To maintain the
previous behavior, explicitly set `frontend.enabled: false`.

### Upgrade from v0.2.0 to v0.3.0

Starting from chart version 0.3.0, the default image repository has changed from `tindy2013/subconverter` to
`asdlokj1qpi23/subconverter`. The new image is functionally equivalent to the previous one.

To continue using the old image repository:

```bash
helm upgrade subconverter charts/subconverter --set image.repository=tindy2013/subconverter
```

To use the new image repository (default):

```bash
helm upgrade subconverter charts/subconverter
```

No other configuration changes are required.

## Uninstalling

```bash
helm uninstall subconverter
```

## Troubleshooting

### Check pod status

```bash
kubectl get pods -l app.kubernetes.io/name=subconverter
```

### View backend logs

```bash
kubectl logs -l app.kubernetes.io/name=subconverter -c subconverter
```

### View frontend logs

```bash
kubectl logs -l app.kubernetes.io/name=subconverter -c subconverter-frontend
```

### Test backend health endpoint

```bash
kubectl exec -it <pod-name> -- curl http://localhost:25500/version
```

### Test frontend health endpoint

```bash
kubectl exec -it <pod-name> -c subconverter-frontend -- curl http://localhost:80/
```

### Frontend Cannot Connect to Backend

If the frontend shows connection errors:

1. **Check if frontend is enabled**:
   ```bash
   kubectl get deployment subconverter -o yaml | grep frontend.enabled
   ```

2. **Verify backend is running**:
   ```bash
   kubectl exec -it <pod-name> -c subconverter -- curl http://localhost:25500/version
   ```

3. **Check API_URL environment variable**:
   ```bash
   kubectl exec -it <pod-name> -c subconverter-frontend -- env | grep API_URL
   ```
   Expected output: `API_URL=http://localhost:25500`

4. **Review frontend logs** for connection errors:
   ```bash
   kubectl logs -l app.kubernetes.io/name=subconverter -c subconverter-frontend --tail=50
   ```

## References

- [Subconverter GitHub](https://github.com/tindy2013/subconverter)
- [Subconverter Documentation](https://github.com/tindy2013/subconverter/blob/master/README-docker.md)
- [sub-web-modify GitHub](https://github.com/youshandefeiyang/sub-web-modify)

## Example Values Files

The chart includes several example values files for different scenarios:

- `values-with-frontend.yaml` - Default configuration with frontend enabled
- `values-no-frontend.yaml` - Backend-only deployment
- `values-external-api.yaml` - Frontend connecting to external API

Usage:

```bash
helm install subconverter charts/subconverter -f charts/subconverter/values-no-frontend.yaml
```
