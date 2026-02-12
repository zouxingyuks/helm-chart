# AxonHub Helm Chart

This Helm chart deploys AxonHub on Kubernetes with MySQL database.

## Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PV provisioner support in the underlying infrastructure (for persistence)

## Installing the Chart

To install the chart with the release name `axonhub`:

```bash
helm install axonhub ./deploy/helm
```

## Configuration

The following table lists the configurable parameters of the AxonHub chart and their default values.

### Global Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.imagePullSecrets` | Global Docker registry secret names as an array | `[]` |

### AxonHub Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `axonhub.replicaCount` | Number of AxonHub replicas | `1` |
| `axonhub.image.repository` | AxonHub image repository | `looplj/axonhub` |
| `axonhub.image.tag` | AxonHub image tag | `latest` |
| `axonhub.image.pullPolicy` | Image pull policy | `IfNotPresent` |
| `axonhub.dbPassword` | Database password | `axonhub_password` |
| `axonhub.service.type` | Kubernetes service type | `ClusterIP` |
| `axonhub.service.port` | Service port | `8090` |
| `axonhub.resources` | CPU/Memory resource requests/limits | `{}` |
| `axonhub.persistence.enabled` | Enable persistence using PVC | `false` |
| `axonhub.persistence.size` | PVC storage request size | `10Gi` |

### MySQL Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `mysql.enabled` | Deploy MySQL chart | `true` |
| `mysql.replicaCount` | Number of MySQL replicas | `1` |
| `mysql.image.repository` | MySQL image repository | `mysql` |
| `mysql.image.tag` | MySQL image tag | `8.0-alpine` |
| `mysql.auth.rootPassword` | MySQL root password | `axonhub_password` |
| `mysql.auth.username` | MySQL user name | `axonhub` |
| `mysql.auth.password` | MySQL user password | `axonhub_password` |
| `mysql.auth.database` | MySQL database name | `axonhub` |
| `mysql.service.type` | Kubernetes service type | `ClusterIP` |
| `mysql.service.port` | MySQL service port | `3306` |
| `mysql.primary.persistence.enabled` | Enable MySQL persistence | `true` |
| `mysql.primary.persistence.size` | PVC storage request size | `8Gi` |

### Ingress Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `ingress.enabled` | Enable ingress controller resource | `false` |
| `ingress.className` | IngressClass that will be used | `""` |
| `ingress.annotations` | Ingress annotations | `{}` |
| `ingress.hosts` | Ingress hostnames | `[{host: axonhub.local, paths: [{path: /, pathType: Prefix}]}]` |
| `ingress.tls` | Ingress TLS configuration | `[]` |

## Database Configuration Options

### Using Internal MySQL (Default)

The chart includes MySQL by default. This is suitable for:
- Development environments
- Small production deployments
- When you want managed database within Kubernetes

```yaml
mysql:
  enabled: true  # Default setting
```

### Using External Database

Disable internal MySQL and configure external database connection:

```yaml
mysql:
  enabled: false

axonhub:
  env:
    AXONHUB_DB_DSN: "username:password@tcp(external-db-host:3306)/database?charset=utf8mb4&parseTime=True&loc=Local"
```

## Production Deployment

For production deployments, you should:

1. Change default passwords:
```yaml
axonhub:
  dbPassword: "your-secure-password"

mysql:
  auth:
    rootPassword: "your-secure-mysql-password"
    password: "your-secure-password"
```

2. Enable persistence:
```yaml
axonhub:
  persistence:
    enabled: true
    size: 20Gi

mysql:
  primary:
    persistence:
      enabled: true
      size: 20Gi
```

3. Configure resource limits:
```yaml
axonhub:
  resources:
    limits:
      cpu: 2000m
      memory: 2Gi
    requests:
      cpu: 1000m
      memory: 1Gi

mysql:
  resources:
    limits:
      cpu: 1000m
      memory: 1Gi
    requests:
      cpu: 500m
      memory: 512Mi
```

4. Enable ingress for external access:
```yaml
ingress:
  enabled: true
  className: "nginx"
  hosts:
    - host: axonhub.yourdomain.com
      paths:
        - path: /
          pathType: Prefix
```

## Upgrading

To upgrade the chart:

```bash
helm upgrade axonhub ./deploy/helm -f values-production.yaml
```

## Uninstalling

To uninstall/delete the release:

```bash
helm uninstall axonhub
```

## Verification

After installation, you can verify the deployment:

```bash
# Check pods status
kubectl get pods

# Check services
kubectl get svc

# Port forward to test
kubectl port-forward svc/axonhub 8090:8090

# Test health endpoint
curl http://localhost:8090/health
```

## Troubleshooting

Common issues and solutions:

1. **Database connection failed**: Check MySQL pod status and logs
2. **Insufficient resources**: Adjust resource requests/limits in values.yaml
3. **Persistent volume issues**: Ensure your cluster has PV provisioner configured
4. **Ingress not working**: Verify ingress controller is installed and configured

## Architecture

The chart deploys:
- AxonHub application as a Deployment
- MySQL database as a StatefulSet
- Services for both components
- Optional ingress for external access
- Persistent volumes for data persistence