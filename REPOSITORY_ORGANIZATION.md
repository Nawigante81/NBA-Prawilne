# Repository Organization Summary

This document summarizes the reorganization of the NBA Analysis repository completed on 2026-01-20.

## Objectives
- Remove temporary and unnecessary files
- Organize files into logical directory structures
- Improve repository maintainability
- Keep essential files accessible in root directory

## Changes Made

### 1. Files Removed
- **Temporary test files**: `tmp-test.bat`, `tmp-test2.bat`
- **Empty error log**: `start.err`
- **Large data files**: `nba historia/` directory (66MB of CSV files)
  - Files moved to local `data/` directory (gitignored)

### 2. New Directory Structure

#### `/docs` - Documentation
Contains detailed guides, historical notes, and platform-specific documentation:
- Feature documentation (ANALYTICS_FEATURES.md, etc.)
- Historical installation docs (INSTALLATION_COMPLETE.md, INSTALLATION_FIX.md)
- Platform-specific guides (MAREKNBA_QUICKSTART.md, OVH_DEPLOYMENT_GUIDE.md, QUICKSTART_OVH.md)
- Docker documentation (DOCKER_BUILD_FIX.md, DOCKER_SETUP.md, DOCKER_OPTIMIZATIONS.md)
- Troubleshooting guides (TROUBLESHOOTING-PI4.md, TROUBLESHOOTING_VENV.md)
- Polish documentation (INSTALACJA_UBUNTU.md, INSTRUKCJA_APLIKACJI.md)
- Project status archive (PROJECT_COMPLETE.md)

#### `/deploy` - Deployment Configurations
Contains Docker, Caddy, and Nginx configurations:
- Docker Compose variants (docker-compose.*.yml)
- Dockerfiles (Dockerfile.frontend, Dockerfile.frontend.pi4)
- Caddyfile variants (Caddyfile.*, multiple platform-specific configs)
- Nginx configurations (nginx.conf, nginx-production.conf)
- PM2 config (ecosystem.config.json)
- Cloudflare Tunnel config (cloudflared.simple.yml)

#### `/scripts` - Scripts and Utilities
Contains deployment, setup, and utility scripts:
- **`/scripts/deploy/`**: Deployment scripts
  - deploy.sh, deploy-caddy.sh, deploy-debian.sh, deploy-mareknba.sh, deploy-ovh.sh, deploy-pi4-arm64.sh
- **`/scripts/setup/`**: Setup scripts
  - setup-native-ubuntu.sh, setup-ovh-vps.sh, setup-pi4-minimal.sh, setup-ssl.sh, setup-ubuntu-mareknba.sh
- **`/scripts/`** (root): Utility scripts
  - caddy-manage.sh, check-pi4-system.sh, fix-caddyfile-v2.sh, fix-caddyfile.sh
  - fix-docker-overlay.sh, optimize-docker-host.sh, quick-fix-caddy.sh
  - monitor.sh, pi-monitor.sh
  - Alternative start/stop scripts (start-caddy.sh, start-native.sh, start-pi4.sh, etc.)
  - Windows batch files (docker-start.bat, docker-stop.bat, start-mini.bat, etc.)

#### `/supabase` - Database Files
SQL setup files moved here:
- supabase_rls_policies.sql
- supabase_setup_complete.sql
- supabase_setup_complete_all_tables.sql
- supabase_setup_simple.sql

### 3. Files Kept in Root
Essential, frequently-used files remain in the root directory:
- **Main documentation**: README.md, INSTALLATION_GUIDE.md, QUICKSTART_WINDOWS.md, WINDOWS_SETUP.md, RASPBERRY_PI_SETUP.md, SUPABASE_SETUP.md, DEPLOYMENT.md, PROJECT_STATUS.md
- **Start/stop scripts**: start.sh, start.bat, stop.sh, stop.bat
- **Setup scripts**: setup.sh, setup.bat
- **Main Docker files**: docker-compose.yml, Dockerfile
- **Configuration**: package.json, tsconfig.json, vite.config.ts, tailwind.config.js, etc.
- **Source code**: src/, backend/, supabase/

### 4. Documentation Updates
- Created README.md files in docs/, deploy/, and scripts/ directories
- Updated main README.md with new project structure
- Updated docker-compose.yml to reference deploy/Dockerfile.frontend
- Updated platform-specific guides (RASPBERRY_PI_SETUP.md, INSTALLATION_GUIDE.md, DEPLOYMENT.md) to reference new paths

### 5. .gitignore Updates
Added entries to ignore:
- `data/` directory (for large data files)
- `*.csv` files
- `*.err` error log files

## Benefits

### Improved Organization
- **Clear separation of concerns**: Documentation, deployment configs, and scripts are in dedicated directories
- **Easier navigation**: Related files are grouped together
- **Reduced clutter**: Root directory is cleaner with only essential files

### Better Maintainability
- **Easier to find files**: Logical directory structure
- **Clear documentation**: README files in each directory explain contents
- **Reduced confusion**: Duplicate and outdated files removed

### Preserved Functionality
- **No breaking changes**: Main scripts (start, stop, setup) still in root
- **Updated references**: All documentation updated to reflect new paths
- **Docker still works**: docker-compose.yml updated to use new paths

## Migration Notes

### For Users
- Main workflow unchanged: `start.sh` / `start.bat` still work from root
- Docker commands unchanged: `docker-compose up -d` still works
- Setup unchanged: `setup.sh` / `setup.bat` still work from root

### For Developers
- Scripts moved to `/scripts` - update any custom scripts
- Docker configs in `/deploy` - use appropriate compose file
- Documentation in `/docs` - check there for detailed guides
- Platform-specific deployments: reference `/deploy` and `/scripts/deploy/`

### Path Updates Required
If you have custom scripts or automation:
- `Dockerfile.frontend` → `deploy/Dockerfile.frontend`
- `docker-compose.*.yml` → `deploy/docker-compose.*.yml`
- `Caddyfile.*` → `deploy/Caddyfile.*`
- Deployment scripts → `scripts/deploy/`
- Setup scripts → `scripts/setup/`

## Statistics
- **Files moved**: 66 files reorganized
- **Files deleted**: 4 files (tmp-test.bat, tmp-test2.bat, start.err, nba historia directory)
- **Space saved**: ~66MB (CSV data files moved to gitignored directory)
- **New directories**: 3 (docs, deploy, scripts with subdirectories)
- **New README files**: 3 (docs/README.md, deploy/README.md, scripts/README.md)

## Validation
✅ Main scripts still work (start.sh, start.bat, setup.sh, setup.bat)
✅ docker-compose.yml updated and valid
✅ Documentation updated with new paths
✅ .gitignore updated to exclude data files
✅ All references to moved files updated

## Future Recommendations
1. Consider adding a `/test` directory for test files if they grow
2. Keep documentation up-to-date as new platforms are supported
3. Archive very old documentation that's no longer relevant
4. Consider using a data management strategy for large CSV files (external storage, LFS, etc.)
