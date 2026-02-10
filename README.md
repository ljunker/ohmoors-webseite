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
