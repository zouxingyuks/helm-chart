# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2025-01-11

### Added
- **Multi-domain Ingress support**: Configure separate domains for frontend and backend with independent TLS certificates and annotations
- New `ingress.hosts` configuration array for multi-domain setup
- Support for per-domain Ingress annotations (CORS, security policies, etc.)
- `values-multi-domain.yaml` example file for quick multi-domain setup
- Updated Service template to expose both frontend (port 80) and backend (port 25500) simultaneously
- Documentation for multi-domain configuration with migration guide

### Changed
- Service now exposes both frontend and backend ports when frontend is enabled
- Updated Ingress template to support both single-domain and multi-domain modes
- Enhanced README with comprehensive multi-domain Ingress documentation

### Backward Compatibility
- Single-domain Ingress configuration (`ingress.hostname`) remains fully functional
- Existing deployments will continue to work without any changes
- Migration to multi-domain mode is optional

## [0.4.0] - 2025-01-11

### Changed
- **BREAKING**: Default frontend image changed from `youshandefeiyang/sub-web-modify`
  to `careywong/subweb` (official upstream)
- Updated documentation to reflect official sub-web frontend
- Updated Chart.yaml sources to point to official repositories

### Added
- Documentation for using third-party frontends (e.g., sub-web-modify)
- Upgrade guide for migrating to official frontend

## [0.3.0] - 2024-XX-XX

### Changed
- Default backend image repository changed from `tindy2013/subconverter` to
  `asdlokj1qpi23/subconverter`

## [0.2.0] - 2024-XX-XX

### Added
- Frontend container support (sub-web-modify)
- Frontend enabled by default

## [0.1.0] - 2024-XX-XX

### Added
- Initial release
- Backend container support
- Basic configuration options
