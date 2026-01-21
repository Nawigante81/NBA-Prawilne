# Ubuntu 24.04 + PM2 (bez Cloudflare, bez Nginx/Caddy)

Wdrozenie produkcyjne z PM2, bez reverse proxy na serwerze. Frontend i backend
sa wystawione bezposrednio na portach przekierowanych na routerze.

## Zalozenia
- Serwer Ubuntu 24.04, lokalne IP: 192.168.100.131
- Publiczne IP/router: 192.168.100.131 (port forwarding na serwer)
- Supabase zewnetrznie (cloud)
- Brak Nginx/Caddy/Docker
- Brak Cloudflare (ruch bezposrednio na porty serwera)

## 1) Porty i przekierowanie (router)
Uzyjemy portow:
- Frontend: 8080
- Backend: 8443

Na routerze ustaw port forwarding na lokalny serwer:
- 192.168.100.131:8080 -> 192.168.100.131:8080
- 192.168.100.131:8443 -> 192.168.100.131:8443

Opcjonalnie, jesli masz domene, ustaw rekordy A (DNS):
- `@` -> 192.168.100.131
- `api` -> 192.168.100.131

## 2) Instalacja zaleznosci (Ubuntu 24.04)
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl build-essential python3 python3-venv python3-pip

# Node.js 20 (LTS)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# PM2
sudo npm install -g pm2
```

## 3) Pobranie projektu
```bash
cd ~
git clone https://github.com/Nawigante81/MarekNBAnalitics--chuj-wi.git nba-analytics
cd nba-analytics
```

## 4) Konfiguracja produkcyjna
Plik `.env.production` ustaw na bezposrednie adresy:
- Bez domeny:
  - `DOMAIN=192.168.100.131`
  - `VITE_API_BASE_URL=http://192.168.100.131:8443`
- Z domena:
  - `DOMAIN=mareknba.pl`
  - `VITE_API_BASE_URL=http://api.mareknba.pl:8443`

Po zmianie wykonaj ponownie build frontendu.

## 5) Build frontendu
```bash
npm ci
npm run build
```

## 6) Backend (Python)
```bash
python3 -m venv backend/venv
source backend/venv/bin/activate
pip install -r backend/requirements.txt
deactivate
```

## 7) Start przez PM2
```bash
mkdir -p logs
pm2 start deploy/ecosystem.pm2.cloudflare.json
pm2 save
pm2 startup
```
Skopiuj i wykonaj komende, ktora wypisze `pm2 startup`.

## 8) Firewall (UFW)
```bash
sudo ufw allow 8080/tcp
sudo ufw allow 8443/tcp
sudo ufw reload
sudo ufw status
```

## 9) Test lokalny na serwerze
```bash
curl http://localhost:8080
curl http://localhost:8443/health
```

## 10) Test z zewnatrz (publiczne IP/DNS)
```bash
curl -I http://192.168.100.131:8080
curl http://192.168.100.131:8443/health
```
Jesli masz domene:
```bash
curl -I http://mareknba.pl:8080
curl http://api.mareknba.pl:8443/health
```

## Zarzadzanie
```bash
pm2 status
pm2 logs nba-backend
pm2 logs nba-frontend
pm2 restart nba-backend
pm2 restart nba-frontend
```

## Najczestsze problemy
- **Frontend pokazuje blad API**: sprawdz `VITE_API_BASE_URL` i zrob `npm run build`.
- **Cloudflare 502**: port forwarding/ufw nie przepuszcza 8080/8443.
- **Backend 401**: `/api/*` wymaga Basic Auth.
- **PM2 frontend nie startuje (bash: run: No such file or directory)**: zrob `pm2 delete nba-frontend`, upewnij sie, ze masz Node.js, uruchom ponownie `pm2 start deploy/ecosystem.pm2.cloudflare.json`.
