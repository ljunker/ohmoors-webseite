# Ohmoor Website

Statische Website mit Build nach `_site`.

## Lokal

```bash
make update_events   # holt neue Termine und schreibt events.json
make build           # baut die Seite nach _site
make serve           # startet lokalen Server auf _site
```

`schedule.html` liest Termine clientseitig aus `events.json` (im Site-Root).
`news.html` liest News clientseitig aus `news.json` (im Site-Root).
`gallery.html` liest Bilder clientseitig aus `gallery-pics/gallery.json` (wird beim Build automatisch aus `static/gallery-pics` erzeugt).

## News verwalten (CRUD)

Lokales Admin-UI:

```bash
python3 scripts/news_admin.py
```

Standard: bearbeitet `static/news.json`.
Optional:

```bash
python3 scripts/news_admin.py --file /pfad/zur/news.json --host 127.0.0.1 --port 8765
```

TUI-Variante:

```bash
python3 scripts/news_tui.py
```

Optional:

```bash
python3 scripts/news_tui.py --file /pfad/zur/news.json
```

## Server-Update nur fuer Events

Script: `scripts/events-update-server.sh`

Standardpfade im Script:
- Projekt: `~/website`
- Deploy: `/var/www/ohmoors.de/html`

Aufruf auf dem Server:

```bash
~/website/scripts/events-update-server.sh
```

Optional mit abweichenden Pfaden:

```bash
PROJECT_ROOT=/pfad/zum/projekt DEPLOY_DIR=/pfad/zum/webroot ~/website/scripts/events-update-server.sh
```

## Serverbetrieb (Debian 13 + Nginx)

Empfohlener Runtime-Job fuer Event-Updates: `scripts/nightly_update.sh`.

Unterstuetzte Variablen:
- `PROJECT_ROOT` (Default: Repo-Root)
- `DEPLOY_DIR` (Default: `/var/www/ohmoors.de/html`)
- `LOCK_FILE` (Default: `/tmp/ohmoors-events.lock`)

Das Script:
- verhindert Parallelstarts via `flock`
- erzeugt `events.json` in einem Temp-Verzeichnis
- validiert JSON vor Deploy
- deployed atomar per `mv`
- schreibt bei vorhandenem Ziel eine Sicherung nach `events.json.last-good`

### Systemd-Timer statt Cron (empfohlen)

Dateien:
- `ops/systemd/ohmoors-events.service`
- `ops/systemd/ohmoors-events.timer`

Beispiel-Installation auf dem Server:

```bash
sudo install -m 0644 ops/systemd/ohmoors-events.service /etc/systemd/system/ohmoors-events.service
sudo install -m 0644 ops/systemd/ohmoors-events.timer /etc/systemd/system/ohmoors-events.timer
sudo systemctl daemon-reload
sudo systemctl enable --now ohmoors-events.timer
sudo systemctl list-timers ohmoors-events.timer
sudo systemctl start ohmoors-events.service
sudo journalctl -u ohmoors-events.service -n 100 --no-pager
```

Legacy-Cron liegt in `ops/ohmoors-nightly.cron`, sollte aber deaktiviert bleiben, wenn der Timer aktiv ist.

### Nginx-Rollout

Die Repo-Datei `ohmoor-squeezers.de` nutzt:
- HTTPS-only
- Canonical Redirect `www -> ohmoor-squeezers.de`
- `events.json` ohne Cache
- Security-/Cache-/Deny-Regeln ueber Snippets in `ops/nginx/snippets/*.conf`

Beispiel-Deployment:

```bash
sudo install -m 0644 ops/nginx/snippets/ohmoors-security.conf /etc/nginx/snippets/ohmoors-security.conf
sudo install -m 0644 ops/nginx/snippets/ohmoors-static-cache.conf /etc/nginx/snippets/ohmoors-static-cache.conf
sudo install -m 0644 ops/nginx/snippets/ohmoors-deny.conf /etc/nginx/snippets/ohmoors-deny.conf
sudo install -m 0644 ohmoor-squeezers.de /etc/nginx/sites-available/ohmoor-squeezers.de
sudo ln -sfn /etc/nginx/sites-available/ohmoor-squeezers.de /etc/nginx/sites-enabled/ohmoor-squeezers.de
sudo nginx -t
sudo systemctl reload nginx
```
