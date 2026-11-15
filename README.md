# Ohmoor Website

Statische Website mit Build nach `_site`.

## Lokal

```bash
make update_events   # holt neue Termine und schreibt events.json
make build           # baut die Seite nach _site
make serve           # startet lokalen Server auf _site
```

### Kalender-Feed-URL

Die URL des iCloud-Kalenders (enthält ein Freigabe-Token) steht nicht im Repo, sondern wird über die Umgebungsvariable `OHMOORS_CALENDAR_URL` übergeben. Ohne sie bricht `events.py` mit Exit-Code 1 ab; bei Abruffehlern mit Exit-Code 2 (ohne `events.json` zu überschreiben).

Lokal:

```bash
OHMOORS_CALENDAR_URL='webcal://...' make update_events
# oder dauerhaft in der Shell:
export OHMOORS_CALENDAR_URL='webcal://...'
```

Server (systemd, `ops/systemd/ohmoors-events.service` liest `EnvironmentFile=/etc/ohmoors/events.env`):

```bash
sudo install -d -m 0755 /etc/ohmoors
echo 'OHMOORS_CALENDAR_URL=webcal://...' | sudo tee /etc/ohmoors/events.env >/dev/null
sudo chown root:root /etc/ohmoors/events.env
sudo chmod 600 /etc/ohmoors/events.env
sudo systemctl daemon-reload
```

Hinweis: Der alte Freigabelink steht noch in der Git-History. Den Freigabelink im iCloud-Kalender daher neu erzeugen (alten widerrufen) und nur die neue URL verwenden.

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

Bei jedem Speichern wird die bisherige Datei als `<name>.bak-<Zeitstempel>` nach `backups/` im Repo (nicht in `static/`) kopiert. Pro Datei werden die neuesten 20 Backups behalten, ältere werden gelöscht. Abweichend einstellbar:

```bash
python3 scripts/news_admin.py --backup-dir /pfad/zu/backups --backup-keep 50
```

`--backup-keep 0` (oder kleiner) deaktiviert das Aufräumen. `scripts/news_tui.py` kennt dieselben Optionen. `make build` kopiert `static/` per `rsync` ohne `*.bak*` und `*.tmp` nach `_site/`.

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
- Backups landen standardmäßig in `<repo>/backups`, der Dienstbenutzer braucht dort (im Checkout) Schreibrechte.
- Einmalig aufräumen: alte Backups `static/*.bak-*` im Checkout löschen oder nach `backups/` verschieben. Der nächste `make deploy` entfernt sie per `--delete` aus dem Webroot.
- Das Rate Limit ist aktuell auf `10` Requests pro Minute pro IP mit `burst=10` gesetzt und antwortet bei Überschreitung mit HTTP `418`. Das schützt gegen stumpfes Durchprobieren, ohne normale Admin-Nutzung unnötig zu stören.

## Server-Update nur fuer Events

Script: `scripts/nightly_update.sh`

Standardpfade (per Umgebungsvariable ueberschreibbar):
- Projekt: Repo-Root des Scripts (auf dem Server `/home/lars/ohmoors-webseite`)
- Deploy: `/var/www/ohmoors.de/html`

Benoetigt `OHMOORS_CALENDAR_URL` (Kalender-Feed-URL), auf dem Server aus `/etc/ohmoors/events.env`.

Aufruf auf dem Server:

```bash
cd /home/lars/ohmoors-webseite
make nightly
# oder direkt:
scripts/nightly_update.sh
```

Optional mit abweichenden Pfaden:

```bash
OHMOORS_CALENDAR_URL=... PROJECT_ROOT=/pfad/zum/projekt DEPLOY_DIR=/pfad/zum/webroot scripts/nightly_update.sh
```

## Serverbetrieb (Debian 13 + Nginx)

Empfohlener Runtime-Job fuer Event-Updates: `scripts/nightly_update.sh`.

Unterstuetzte Variablen:
- `PROJECT_ROOT` (Default: Repo-Root)
- `DEPLOY_DIR` (Default: `/var/www/ohmoors.de/html`)
- `LOCK_FILE` (Default: `/tmp/ohmoors-events.lock`; die systemd-Unit setzt `/run/ohmoors-events/update.lock`)
- `OHMOORS_CALENDAR_URL` (Pflicht, Kalender-Feed-URL)

Das Script:
- verhindert Parallelstarts via `flock`
- erzeugt `events.json` in einem Temp-Verzeichnis
- validiert JSON vor Deploy
- deployed atomar per `mv`
- schreibt bei vorhandenem Ziel eine Sicherung nach `events.json.last-good`

Hinweis zu `make deploy`: Der Deploy fasst `events.json` und `events.json.last-good` im Webroot nicht an (rsync-Excludes, auch bei `--delete`). Nur beim Erst-Deploy, wenn im Webroot noch keine `events.json` existiert, wird die gebaute Datei einmalig kopiert. Danach werden beide Dateien ausschliesslich vom nächtlichen Job gepflegt. Für sofort aktuelle Termine `make nightly` (bzw. `scripts/nightly_update.sh`) ausführen.

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

Die Unit laeuft als `User=lars`/`Group=lars` mit Checkout `/home/lars/ohmoors-webseite` und eigenem Lock unter `/run/ohmoors-events/`. Es gibt keinen Cron-Job mehr; der Timer ist der einzige Scheduler.

Migration bestehender Installationen (Dienst lief bisher als root bzw. mit falschen Pfaden):

```bash
sudo install -m 0644 ops/systemd/ohmoors-events.service /etc/systemd/system/ohmoors-events.service
sudo systemctl daemon-reload
sudo chown lars:lars /var/www/ohmoors.de/html/events.json /var/www/ohmoors.de/html/events.json.last-good  # falls vorhanden
sudo rm -f /tmp/ohmoors-events.lock
sudo crontab -l   # evtl. noch aktiven Root-Cron-Eintrag fuer nightly_update.sh mit `sudo crontab -e` entfernen
sudo systemctl start ohmoors-events.service
```

### Nginx-Rollout

Die Repo-Datei `ohmoor-squeezers.de` nutzt:
- HTTPS-only
- Canonical Redirect `www -> ohmoor-squeezers.de`
- `events.json` ohne Cache
- Security-/Cache-/Deny-Regeln ueber Snippets in `ops/nginx/snippets/*.conf`
- Hinweis: nginx vererbt `add_header` nur an Locations ohne eigenes `add_header`; Locations mit eigenem `add_header` (Asset-Cache, `events.json`) binden `ohmoors-security.conf` deshalb selbst ein. Das Deny-Snippet muss vor dem Cache-Snippet stehen (Regex-Locations: erster Treffer gewinnt).

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
