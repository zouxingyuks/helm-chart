# Claude Relay Service Helm Chart

A Helm chart for deploying Claude Relay Service with internal Redis cluster support.

## 🚀 Features

- ✅ **Internal Redis Cluster**: Production-ready Redis with Bitnami chart
- ✅ **Production Ready**: Complete security, monitoring, and scaling configurations
- ✅ **Environment Variable Driven**: Fully compatible with official Claude Relay Service config
- ✅ **Startup Dependencies**: Application waits for Redis to be ready
- ✅ **Flexible Authentication**: Support for JWT, admin credentials, and LDAP
- ✅ **Comprehensive Logging**: Configurable log levels and file rotation
- ✅ **Load Balancing**: Kubernetes Ingress and Service support
- ✅ **Resource Management**: CPU, memory, and storage limits
- ✅ **High Availability**: Multi-replica Redis with StatefulSets

## 📋 Prerequisites

- Kubernetes 1.19+
- Helm 3.0+
- PVC (optional, only for Redis persistence)

## 🔧 Installation

### Basic Installation (Internal Redis)

```bash
# Install with default internal Redis
helm install claude-relay ./claude-relay-service \
  --namespace claude-relay-service \
  --create-namespace \
  --set redis.auth.password=your-redis-password \
  --set env.JWT_SECRET=your-jwt-secret \
  --set env.ENCRYPTION_KEY=your-encryption-key \
  --set env.ADMIN_USERNAME=admin \
  --set env.ADMIN_PASSWORD=admin-password
```


### Production Installation

```bash
# Install for production with Ingress and scaling
helm install claude-relay ./claude-relay-service \
  --namespace claude-relay-service \
  --create-namespace \
  --set redis.enabled=true \
  --set redis.auth.password=strong-redis-password \
  --set redis.master.persistence.enabled=true \
  --set redis.master.persistence.size=20Gi \
  --set replicaCount=3 \
  --set resources.requests.cpu=500m \
  --set resources.requests.memory=512Mi \
  --set resources.limits.cpu=1000m \
  --set resources.limits.memory=1Gi \
  --set autoscaling.enabled=true \
  --set autoscaling.minReplicas=2 \
  --set autoscaling.maxReplicas=10 \
  --set autoscaling.targetCPUUtilizationPercentage=70 \
  --set ingress.enabled=true \
  --set ingress.hostname=claude-relay.example.com \
  --set env.JWT_SECRET=your-production-jwt-secret \
  --set env.ENCRYPTION_KEY=your-production-encryption-key \
  --set env.ADMIN_USERNAME=admin \
  --set env.ADMIN_PASSWORD=strong-admin-password \
  --set env.NODE_ENV=production
```

## ⚙️ Configuration

### 🔐 Security Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|----------|---------|
| `env.JWT_SECRET` | JWT signing secret | Random | `your-super-secret-jwt-key` |
| `env.ENCRYPTION_KEY` | Data encryption key | Random | `your-32-character-encryption-key` |
| `env.ADMIN_SESSION_TIMEOUT` | Admin session timeout (ms) | `86400000` | `86400000` (24h) |
| `env.ADMIN_USERNAME` | Default admin username | Empty | `admin` |
| `env.ADMIN_PASSWORD` | Default admin password | Empty | `secure-password` |
| `env.API_KEY_PREFIX` | API key prefix | `cr_` | `myapp_` |

### 🤖 Claude API Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|----------|---------|
| `env.CLAUDE_API_URL` | Claude API endpoint | `https://api.anthropic.com/v1/messages` | Custom endpoint |
| `env.CLAUDE_API_VERSION` | API version | `2023-06-01` | `2024-01-01` |
| `env.CLAUDE_BETA_HEADER` | Beta features header | Complex string | Custom features |

### 🌐 Server Configuration

| Parameter | Description | Default | Example |
|-----------|-------------|----------|---------|
| `env.PORT` | Application port | `3000` | `8080` |
| `env.HOST` | Bind host | `0.0.0.0` | `127.0.0.1` |
| `env.NODE_ENV` | Node environment | `production` | `development` |
| `env.TRUST_PROXY` | Trust proxy headers | `false` | `true` |

### 📊 Redis Configuration

#### Internal Redis (Default)

```yaml
redis:
  enabled: true
  auth:
    enabled: true
    password: "your-redis-password"
  master:
    persistence:
      enabled: false  # Set to true for production
  replica:
    replicaCount: 1  # Increase for HA
    persistence:
      enabled: false
```

### 👥 LDAP Authentication (Optional)

```yaml
env:
  LDAP_ENABLED: "true"
  LDAP_URL: "ldap://ldap.example.com:389"
  LDAP_BIND_DN: "cn=admin,dc=example,dc=com"
  LDAP_BIND_PASSWORD: "ldap-password"
  LDAP_SEARCH_BASE: "dc=example,dc=com"
  LDAP_SEARCH_FILTER: "(uid={{username}})"
  LDAP_SEARCH_ATTRIBUTES: "dn,uid,cn,mail,givenName,sn"
  LDAP_USER_ATTR_USERNAME: "uid"
  LDAP_USER_ATTR_DISPLAY_NAME: "cn"
  LDAP_USER_ATTR_EMAIL: "mail"
```

### 🌐 Ingress Configuration

```yaml
ingress:
  enabled: true
  hostname: "claude-relay.example.com"
  path: "/"
  className: "nginx"
  tls:
    enabled: true
    secretName: "claude-relay-tls"
```

### 📈 Scaling Configuration

```yaml
# Horizontal Pod Autoscaling
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80

# Pod Disruption Budget
podDisruptionBudget:
  enabled: true
  minAvailable: 1
  maxUnavailable: 1
```

## 🔍 Values Reference

Complete configuration options are available in [values.yaml](./values.yaml).

## 📊 Monitoring and Logging

### Health Checks

The application includes comprehensive health checks:

```yaml
healthCheck:
  path: "/health"
  interval: "30s"
  timeout: "10s"
  retries: 3
```

### Logging

Configurable logging with rotation:

```yaml
env:
  LOG_LEVEL: "info"  # debug, info, warn, error
  LOG_MAX_SIZE: "10m"
  LOG_MAX_FILES: "5"
```

## 🚨 Troubleshooting

### Common Issues

1. **Redis Connection Failed**
   ```bash
   # Check Redis logs
   kubectl logs -n claude-relay-service -l app.kubernetes.io/name=redis -c redis

   # Check application startup logs
   kubectl logs -n claude-relay-service -l app.kubernetes.io/name=claude-relay-service -c claude-relay
   ```

2. **PVC Issues**
   ```bash
   # Check available storage classes
   kubectl get storageclass

   # Use external Redis if storage is not available
   helm upgrade claude-relay ./claude-relay-service \
     --set redis.external.enabled=true \
     --set redis.external.host=your-redis-host
   ```

3. **Authentication Issues**
   ```bash
   # Verify admin credentials
   kubectl get secret claude-relay-service -n claude-relay-service -o yaml

   # Check JWT secret
   echo "JWT_SECRET=$(kubectl get secret claude-relay-service -n claude-relay-service -o jsonpath='{.data.jwt-secret}' | base64 -d)"
   ```

## 🔄 Upgrading

```bash
# Upgrade with preserved values
helm upgrade claude-relay ./claude-relay-service \
  --namespace claude-relay-service \
  --reuse-values

# Upgrade with new values
helm upgrade claude-relay ./claude-relay-service \
  --namespace claude-relay-service \
  --set replicaCount=2 \
  --set redis.external.enabled=true
```

## 🗑️ Uninstalling

```bash
helm uninstall claude-relay --namespace claude-relay-service
```

## 📝️ Development

For development environments:

```bash
# Development mode with debugging
helm install claude-relay-dev ./claude-relay-service \
  --namespace claude-relay-service-dev \
  --create-namespace \
  --set env.NODE_ENV=development \
  --set env.DEBUG=true \
  --set env.HOT_RELOAD=true \
  --set replicaCount=1 \
  --set redis.master.persistence.enabled=false \
  --set redis.replica.persistence.enabled=false
```

## 🤝 Contributing

This Helm chart follows best practices:
- Uses official Bitnami charts for dependencies
- Implements proper security contexts
- Includes comprehensive health checks
- Supports multiple deployment scenarios
- Follows Kubernetes naming conventions

## 📄 License

This Helm chart is licensed under the same terms as the Claude Relay Service.

## 🆘 Support

For issues and support:
1. Check the [troubleshooting guide](#-troubleshooting)
2. Verify configuration against [values.yaml](./values.yaml)
3. Check Kubernetes cluster connectivity
4. Review pod logs for detailed error messages