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

Standard: bearbeitet `static/news.json` und die Vorlagen in `static/news_templates.json`.
`text` in den News-Eintraegen unterstuetzt Markdown fuer Absätze, Listen, Links sowie einfache Hervorhebungen.
Das Admin-UI zeigt beim Bearbeiten eine Live-Vorschau des Markdown-Renderings an.
Vorlagen können separat gepflegt und per Button in die News kopiert werden; bestehende News lassen sich ebenfalls als Vorlage kopieren.
Zusätzlich gibt es Buttons für `Git add/commit/push` von `news.json` und `news_templates.json` sowie für ein direktes Deploy von `news.json` ins Webroot.
Einträge können optional über `published_from` und `published_until` zeitlich gesteuert werden. Auf der Admin-Seite gibt es dafür Kalenderfelder; leer bedeutet sofort bzw. unbegrenzt sichtbar.
Optional:

```bash
python3 scripts/news_admin.py --file /pfad/zur/news.json --templates-file /pfad/zur/news_templates.json --host 127.0.0.1 --port 8765
```

Optional mit abweichendem Deploy-Ziel:

```bash
python3 scripts/news_admin.py --deploy-dir /pfad/zum/webroot
```

Standard-Deploy-Ziel: `/var/www/ohmoors.de/html`

TUI-Variante:

```bash
python3 scripts/news_tui.py
```

Optional:

```bash
python3 scripts/news_tui.py --file /pfad/zur/news.json
```

### News Admin auf dem Server

Empfohlener Betrieb:
- `scripts/news_admin.py` per `systemd` als dauerhaften Dienst starten
- Dienst nur auf `127.0.0.1:8765` binden
- Zugriff ausschließlich über Nginx-Reverse-Proxy mit Passwortschutz
- `Restart=on-failure` verwenden, damit der Dienst bei Fehlern automatisch neu startet

Beispiel-Unit:
- `ops/systemd/ohmoors-news-admin.service`

Beispiel-Nginx-Snippet:
- `ops/nginx/snippets/ohmoors-news-admin.conf`
- `ops/nginx/ohmoors-news-admin-rate-limit.conf` fuer die globale Rate-Limit-Zone im `http`-Kontext

Beispiel-Installation auf dem Server:

```bash
sudo install -m 0644 ops/nginx/ohmoors-news-admin-rate-limit.conf /etc/nginx/conf.d/ohmoors-news-admin-rate-limit.conf
sudo install -m 0644 ops/systemd/ohmoors-news-admin.service /etc/systemd/system/ohmoors-news-admin.service
sudo install -m 0644 ops/nginx/snippets/ohmoors-news-admin.conf /etc/nginx/snippets/ohmoors-news-admin.conf
sudo systemctl daemon-reload
sudo systemctl enable --now ohmoors-news-admin.service
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl status ohmoors-news-admin.service --no-pager
sudo journalctl -u ohmoors-news-admin.service -n 100 --no-pager
```

Passwortdatei für Admin-Zugang anlegen:

```bash
sudo apt-get install -y apache2-utils
sudo htpasswd -B -C 15 -c /etc/nginx/.htpasswd-ohmoors-admin ADMINNAME
```

Geschützte URL:

```text
https://ohmoor-squeezers.de/admin/news/
```

Wichtig:
- Die `systemd`-Unit sollte unter dem Deploy-/Admin-Benutzer laufen, der den Repo-Checkout besitzt.
- Dieser Benutzer braucht funktionierende Git-Credentials für `git push`.
- Dieser Benutzer braucht Schreibrechte auf `/var/www/ohmoors.de/html`.
- Für den aktuellen Server-Stand sind `User=lars`, `Group=lars` und `WorkingDirectory=/home/lars/ohmoors-webseite` vorgesehen.
- Passe nur dann `User=`, `Group=`, `WorkingDirectory=`, `NEWS_FILE=`, `NEWS_TEMPLATES_FILE=` oder den Python-Pfad an, wenn dein Server davon abweicht.
- Das Rate Limit ist aktuell auf `10` Requests pro Minute pro IP mit `burst=10` gesetzt und antwortet bei Überschreitung mit HTTP `418`. Das schützt gegen stumpfes Durchprobieren, ohne normale Admin-Nutzung unnötig zu stören.

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
