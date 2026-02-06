# Ohmoor Website

Statische Website mit Build nach `_site`.

## Lokal

```bash
make update_events   # holt neue Termine und schreibt events.json
make build           # baut die Seite nach _site
make serve           # startet lokalen Server auf _site
```

`schedule.html` liest Termine clientseitig aus `events.json` (im Site-Root).

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
