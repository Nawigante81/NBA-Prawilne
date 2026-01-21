# Deploy Directory

This directory contains deployment configurations and Docker-related files for various deployment scenarios.

## Structure

### Docker Compose Files
- `docker-compose.yml` - **Main production compose file** (also in root)
- `docker-compose.local.yml` - Local development configuration
- `docker-compose.prod.yml` - Production configuration variant
- `docker-compose.pi4.yml` - Raspberry Pi 4 configuration
- `docker-compose-caddy.yml` - Configuration with Caddy reverse proxy

### Dockerfiles
- `Dockerfile` - **Main backend Dockerfile** (also in root)
- `Dockerfile.frontend` - Frontend production build
- `Dockerfile.frontend.pi4` - Frontend for Raspberry Pi 4

### Web Server Configurations

#### Caddy
- `Caddyfile` - Main Caddy configuration
- `Caddyfile.docker` - Docker-specific Caddy config
- `Caddyfile.simple` - Simplified Caddy config
- `Caddyfile.corrected` - Corrected Caddy config
- `Caddyfile.v2-corrected` - Caddy v2 corrected config
- `Caddyfile.pi4` - Raspberry Pi 4 Caddy config

#### Nginx
- `nginx.conf` - Main Nginx configuration
- `nginx-production.conf` - Production Nginx configuration

### Other Configurations
- `ecosystem.config.json` - PM2 process manager configuration
- `cloudflared.simple.yml` - Cloudflare Tunnel configuration

## Main Files

The following files are kept in the **root directory** for convenience:
- `docker-compose.yml` - Most commonly used Docker Compose file
- `Dockerfile` - Main backend Dockerfile

## Usage

### Using Docker Compose
```bash
# From project root
docker-compose up -d

# Using a specific compose file
docker-compose -f deploy/docker-compose.local.yml up -d
```

### Building Docker Images
```bash
# Backend
docker build -t nba-backend -f Dockerfile ./backend

# Frontend
docker build -t nba-frontend -f deploy/Dockerfile.frontend .
```

### Caddy Configuration
Copy the appropriate Caddyfile to your Caddy configuration directory:
```bash
# For Docker
cp deploy/Caddyfile.docker /etc/caddy/Caddyfile

# For Raspberry Pi 4
cp deploy/Caddyfile.pi4 /etc/caddy/Caddyfile
```

### Nginx Configuration
```bash
# Copy to Nginx sites-available
cp deploy/nginx-production.conf /etc/nginx/sites-available/nba
ln -s /etc/nginx/sites-available/nba /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

## Platform-Specific Notes

### Raspberry Pi 4
- Use `docker-compose.pi4.yml` for ARM64 architecture
- Use `Dockerfile.frontend.pi4` for optimized frontend builds
- Use `Caddyfile.pi4` for Pi-specific Caddy configuration

### Local Development
- Use `docker-compose.local.yml` for local development
- Includes hot-reload and development-specific settings

### Production Deployment
- Use main `docker-compose.yml` or `docker-compose.prod.yml`
- Configure SSL certificates with Caddy or Nginx
- Set appropriate environment variables in `.env.production`
