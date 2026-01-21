# Scripts Directory

This directory contains utility scripts, deployment scripts, and alternative startup scripts for the NBA Analysis project.

## Structure

### Main Scripts (in root directory)
The most commonly used scripts are kept in the root for convenience:
- `start.sh` / `start.bat` - Main startup script (Linux/Windows)
- `stop.sh` / `stop.bat` - Main stop script (Linux/Windows)
- `setup.sh` / `setup.bat` - Setup and installation script (Linux/Windows)

### Deployment Scripts (`deploy/`)
Scripts for deploying to various platforms:
- `deploy.sh` - Main deployment script
- `deploy-caddy.sh` - Caddy-specific deployment
- `deploy-debian.sh` - Debian/Ubuntu deployment
- `deploy-mareknba.sh` - MarekNBA specific deployment
- `deploy-ovh.sh` - OVH VPS deployment
- `deploy-pi4-arm64.sh` - Raspberry Pi 4 ARM64 deployment

### Setup Scripts (`setup/`)
Platform-specific setup scripts:
- `setup-native-ubuntu.sh` - Native Ubuntu setup
- `setup-ovh-vps.sh` - OVH VPS setup
- `setup-pi4-minimal.sh` - Minimal Raspberry Pi 4 setup
- `setup-ssl.sh` - SSL certificate setup
- `setup-ubuntu-mareknba.sh` - Ubuntu MarekNBA setup

### Utility Scripts (root of scripts/)
Various utility and helper scripts:
- `caddy-manage.sh` - Caddy management utilities
- `check-pi4-system.sh` - Raspberry Pi 4 system checks
- `fix-caddyfile-v2.sh` - Caddyfile v2 fixes
- `fix-caddyfile.sh` - General Caddyfile fixes
- `fix-docker-overlay.sh` - Docker overlay filesystem fixes
- `optimize-docker-host.sh` - Docker host optimization
- `quick-fix-caddy.sh` - Quick Caddy fixes
- `monitor.sh` - System monitoring
- `pi-monitor.sh` - Raspberry Pi monitoring

### Alternative Start/Stop Scripts
Platform or configuration-specific startup scripts:
- `start-caddy.sh` - Start with Caddy
- `start-native.sh` - Native (non-Docker) startup
- `start-pi4.sh` - Raspberry Pi 4 startup
- `start-simple.sh` - Simple/minimal startup
- `stop-native.sh` - Stop native processes
- `stop-simple.sh` - Simple stop

### Windows Batch Scripts
- `docker-start.bat` - Docker startup (Windows)
- `docker-stop.bat` - Docker stop (Windows)
- `start-mini.bat` - Minimal Windows startup
- `start-norem.bat` - Windows startup without remote
- `upload-to-server.bat` - Upload files to server

## Usage

All scripts should be run from the **project root directory**.

For daily use:
```bash
# Linux/macOS
./start.sh     # Start the application
./stop.sh      # Stop the application

# Windows
start.bat      # Start the application
stop.bat       # Stop the application
```

For deployment or specific platforms, use the appropriate script from the subdirectories:
```bash
# Example: Deploy to OVH
./scripts/deploy/deploy-ovh.sh

# Example: Setup on Raspberry Pi
./scripts/setup/setup-pi4-minimal.sh
```
