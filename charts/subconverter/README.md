# Subconverter Helm Chart

## Introduction

Subconverter is a utility to convert between various proxy subscription formats. It supports conversion between Clash,
V2Ray, Surge, Quantumult X, and many other popular proxy clients.

This Helm chart deploys a complete subconverter instance on Kubernetes with:

- **Backend**: Subconverter API service for subscription conversion
- **Frontend**: [sub-web](https://github.com/CareyWang/sub-web) web UI for subscription conversion

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

| Parameter                   | Description                                  | Default                  |
|-----------------------------|----------------------------------------------|--------------------------|
| `frontend.enabled`          | Enable frontend container                    | `true`                   |
| `frontend.image.repository` | Frontend image repository                    | `careywong/subweb`       |
| `frontend.image.tag`        | Frontend image tag                           | `latest`                 |
| `frontend.apiURL`           | External API URL (empty = use local backend) | `""`                     |
| `frontend.projectUrl`       | Project homepage URL (VUE_APP_PROJECT)       | `https://github.com/CareyWang/sub-web` |
| `frontend.botLink`          | Telegram bot link (VUE_APP_BOT_LINK)         | `https://t.me/subconverter_discuss` |
| `frontend.useStorage`       | Use browser storage (VUE_APP_USE_STORAGE)    | `true`                   |
| `frontend.cacheTTL`         | Cache time-to-live in seconds (VUE_APP_CACHE_TTL) | `86400`            |
| `frontend.backendRelease`   | Backend release page link (VUE_APP_BACKEND_RELEASE) | `https://github.com/tindy2013/subconverter/actions` |
| `frontend.remoteConfig`     | Remote config file URL (VUE_APP_SUBCONVERTER_REMOTE_CONFIG) | `https://raw.githubusercontent.com/tindy2013/subconverter/master/base/config/example_external_config.ini` |
| `frontend.advancedDoc`      | Advanced documentation link (VUE_APP_SUBCONVERTER_DOC_ADVANCED) | `https://github.com/tindy2013/subconverter/blob/master/README-cn.md#%E8%BF%9B%E9%98%B6%E9%93%BE%E6%8E%A5` |
| `frontend.myurlsApi`        | Short URL backend API (VUE_APP_MYURLS_API)   | `""` (disabled by default) |
| `frontend.configUploadApi`  | Configuration upload API (VUE_APP_CONFIG_UPLOAD_API) | `""` (disabled by default) |
| `frontend.env`              | Additional environment variables             | `[]`                     |
| `frontend.resources`        | Frontend resource limits/requests            | See below                |

#### Frontend Environment Variables

The frontend container uses **Vue.js environment variables**. All custom environment variables in Vue.js must start with `VUE_APP_` to be available in the application.

**Important**: Only environment variables starting with `VUE_APP_` will be recognized by the Vue.js application. Variables without this prefix (like the old `API_URL`) are ignored by Vue.js.

**Configurable Variables**:

| Environment Variable | Description | Default | Configuration Parameter |
|---------------------|-------------|---------|------------------------|
| `VUE_APP_SUBCONVERTER_DEFAULT_BACKEND` | Backend API URL | `http://localhost:25500` | `frontend.apiURL` |
| `VUE_APP_PROJECT` | Project homepage | `https://github.com/CareyWang/sub-web` | `frontend.projectUrl` |
| `VUE_APP_BOT_LINK` | Telegram bot link | `https://t.me/subconverter_discuss` | `frontend.botLink` |
| `VUE_APP_USE_STORAGE` | Enable browser storage | `true` | `frontend.useStorage` |
| `VUE_APP_CACHE_TTL` | Cache TTL in seconds | `86400` | `frontend.cacheTTL` |
| `VUE_APP_BACKEND_RELEASE` | Backend release page link | `https://github.com/tindy2013/subconverter/actions` | `frontend.backendRelease` |
| `VUE_APP_SUBCONVERTER_REMOTE_CONFIG` | Remote config file URL | `https://raw.githubusercontent.com/tindy2013/subconverter/master/base/config/example_external_config.ini` | `frontend.remoteConfig` |
| `VUE_APP_SUBCONVERTER_DOC_ADVANCED` | Advanced documentation link | `https://github.com/tindy2013/subconverter/blob/master/README-cn.md#%E8%BF%9B%E9%98%B6%E9%93%BE%E6%8E%A5` | `frontend.advancedDoc` |
| `VUE_APP_MYURLS_API` | Short URL backend API | `""` (disabled) | `frontend.myurlsApi` |
| `VUE_APP_CONFIG_UPLOAD_API` | Configuration upload API | `""` (disabled) | `frontend.configUploadApi` |

**Additional Variables**:

You can add extra custom environment variables using the `frontend.env` array. All custom environment variables must start with `VUE_APP_` prefix.

Example:

```yaml
frontend:
  env:
    - name: VUE_APP_CUSTOM_VAR
      value: "custom-value"
```

See [Vue CLI documentation](https://cli.vuejs.org/guide/mode-and-env.html#using-env-variables-in-client-side-code) for more details.

#### Frontend Security

The frontend container uses the default security context from the original Docker image
(`careywong/subweb`). This chart avoids over-engineering security configurations to maintain
compatibility with the upstream image design.

If you need custom security settings, you can override `frontend.securityContext` in your
values file.

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

**Chart v0.4.0+: Conditional Port Exposure**

When frontend is enabled, the service exposes only the frontend port:

- **Port 80** (named `http`): Frontend web UI - Use this for accessing the web interface
  - **targetPort: 80** - Routes traffic specifically to the frontend container
- The backend port (25500) is NOT exposed through the service for security reasons
- The frontend container accesses the backend via `http://localhost:25500` within the Pod

When frontend is disabled, the service exposes only the backend port:

- **Port 25500** (named `backend`): Backend API - Use this for direct API access
  - **targetPort: 25500** - Routes traffic specifically to the backend container
- This configuration is suitable for API-only deployments

**Note on targetPort**: The service uses explicit port numbers (80, 25500) as `targetPort` instead of port names. This ensures precise traffic routing to the correct container when multiple containers are present in the Pod, avoiding potential routing conflicts.

**Migration from v0.3.x and earlier**: In previous versions, both ports were exposed when frontend was enabled. If you were directly accessing the backend port through the service, you have two options:
1. Keep frontend enabled and access the backend through the frontend web UI
2. Disable frontend (`frontend.enabled: false`) to expose only the backend port

#### Accessing the Services

```bash
# When frontend is enabled (default)
kubectl port-forward svc/subconverter 8080:80
# Open browser at http://localhost:8080

# When frontend is disabled
kubectl port-forward svc/subconverter 25500:25500
# Test: curl http://localhost:25500/version
```

### Ingress Configuration

The chart supports two Ingress configuration modes:

| Parameter           | Description               | Default                    |
|---------------------|---------------------------|----------------------------|
| `ingress.enabled`   | Enable ingress            | `false`                    |
| `ingress.className` | Ingress class name        | `nginx`                    |
| `ingress.hostname`  | Ingress hostname (single domain mode) | `subconverter.example.com` |
| `ingress.hosts`     | Multiple domain configurations (multi-domain mode) | `[]` |
| `ingress.tls`       | Ingress TLS configuration (single domain mode) | `[]` |

#### Ingress Behavior

By default, when frontend is enabled, the Ingress routes traffic to the frontend (port 80). Users can access the web UI
through the Ingress hostname.

#### Multi-Domain Ingress (NEW)

The chart now supports configuring multiple domains with independent TLS certificates and annotations for frontend and backend:

**Example: Separate domains for frontend and backend**

```yaml
ingress:
  enabled: true
  className: "nginx"
  hostname: ""  # Leave empty when using multi-domain mode

  hosts:
    # Frontend domain
    - name: frontend.example.com
      servicePort: 80  # Routes to frontend container
      path: /
      pathType: Prefix
      annotations:
        cert-manager.io/cluster-issuer: "letsencrypt-prod"
      tls:
      - secretName: frontend-tls
        hosts:
          - frontend.example.com

    # Backend API domain
    - name: api.example.com
      servicePort: 25500  # Routes to backend API
      path: /
      pathType: Prefix
      annotations:
        cert-manager.io/cluster-issuer: "letsencrypt-prod"
        nginx.ingress.kubernetes.io/cors-allow-origin: "https://frontend.example.com"
        nginx.ingress.kubernetes.io/enable-cors: "true"
      tls:
      - secretName: api-tls
        hosts:
          - api.example.com
```

**Benefits of multi-domain mode**:
- Separate domain names for frontend UI and backend API
- Independent TLS certificates for each domain
- Different Ingress annotations per domain (CORS, security policies, etc.)
- Better security and isolation

Use the provided example file for quick setup:
```bash
helm install subconverter charts/subconverter -f charts/subconverter/values-multi-domain.yaml
```

**Migration from single-domain mode**:
```yaml
# Before (single domain)
ingress:
  hostname: subconverter.example.com

# After (multi-domain)
ingress:
  hostname: ""  # Clear this
  hosts:
    - name: frontend.example.com
      servicePort: 80
    - name: api.example.com
      servicePort: 25500
```

#### Separate Ingress for Frontend and Backend (Legacy)

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

### Using Third-Party Frontend

If you prefer to use the enhanced sub-web-modify frontend with additional features
like dark mode and more remote configurations:

```bash
helm install subconverter charts/subconverter \
  --set frontend.image.repository=youshandefeiyang/sub-web-modify \
  --set frontend.image.tag=latest
```

Or create a custom values file:

```yaml
frontend:
  image:
    repository: youshandefeiyang/sub-web-modify
    tag: latest
```

**Note**: The default frontend is the official CareyWang/sub-web, which provides
core functionality without additional modifications.

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

### Upgrade from v0.3.0 to v0.4.0

**Important Breaking Change: Service Port Configuration**

Starting from chart version 0.4.0, the Service port exposure behavior has changed for improved security:

- **Previous behavior (v0.3.x)**: When frontend was enabled, the service exposed both port 80 (frontend) and port 25500 (backend)
- **New behavior (v0.4.0+)**:
  - When `frontend.enabled: true`, the service exposes **only port 80** (frontend)
  - When `frontend.enabled: false`, the service exposes **only port 25500** (backend)

**Rationale**: This change follows Kubernetes best practices where containers in the same Pod should communicate via `localhost`. The backend port doesn't need to be exposed through the service since the frontend accesses it internally.

**Migration Guide**:

If you have an existing deployment with frontend enabled and you were directly accessing the backend port through the service:

1. **Option 1**: Access the backend through the frontend web UI (recommended)
   ```bash
   helm upgrade subconverter charts/subconverter
   # Access via http://<your-ingress-host>/ or port-forward to port 80
   ```

2. **Option 2**: Disable the frontend to expose only the backend port
   ```bash
   helm upgrade subconverter charts/subconverter --set frontend.enabled=false
   ```

**Frontend Image Update**:

In v0.4.0, the default frontend image has also changed from `youshandefeiyang/sub-web-modify` to `careywong/subweb`.

The official `careywong/subweb` image provides the core sub-web functionality without additional modifications. It is maintained by the upstream author and has better long-term support.

**To upgrade to the new frontend (recommended)**:

```bash
helm upgrade subconverter charts/subconverter
```

**To continue using the old frontend**:

```bash
helm upgrade subconverter charts/subconverter \
  --set frontend.image.repository=youshandefeiyang/sub-web-modify
```

**Key differences**:
- Official version does not include dark mode
- Official version has fewer preset remote configurations (you can add your own)
- Official version is actively maintained by the upstream author

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
- [sub-web GitHub](https://github.com/CareyWang/sub-web)

## Example Values Files

The chart includes several example values files for different scenarios:

- `values-with-frontend.yaml` - Default configuration with frontend enabled
- `values-no-frontend.yaml` - Backend-only deployment
- `values-external-api.yaml` - Frontend connecting to external API

Usage:

```bash
helm install subconverter charts/subconverter -f charts/subconverter/values-no-frontend.yaml
```
