SITE_DIR := _site
STATIC_DIR := static
EVENTS_JSON := events.json
EVENTS_PY := events.py
PYTHON := .venv/bin/python3
DEPLOY_DIR ?= /var/www/ohmoors.de/html
NIGHTLY_SCRIPT := scripts/nightly_update.sh
GALLERY_MANIFEST_SCRIPT := scripts/build_gallery_manifest.py
GALLERY_PICS_DIR := $(STATIC_DIR)/gallery-pics
GALLERY_MANIFEST := $(SITE_DIR)/gallery-pics/gallery.json

.PHONY: all build copy_static copy_events_json copy_gallery_manifest clean serve deploy nightly update_events

all: build

build: copy_static copy_events_json copy_gallery_manifest build_pages

jesus: clean build

love: build serve

it_so: clean_all build serve

copy_static:
	@mkdir -p $(SITE_DIR)
	@rsync -a --exclude '*.bak*' --exclude '*.tmp' $(STATIC_DIR)/ $(SITE_DIR)/

copy_events_json: $(EVENTS_JSON)
	@mkdir -p $(SITE_DIR)
	@cp $(EVENTS_JSON) $(SITE_DIR)/$(EVENTS_JSON)

copy_gallery_manifest:
	@mkdir -p $(SITE_DIR)/gallery-pics
	@$(PYTHON) $(GALLERY_MANIFEST_SCRIPT) --images-dir $(GALLERY_PICS_DIR) --output $(GALLERY_MANIFEST)

update_events: $(EVENTS_JSON)

$(EVENTS_JSON): $(EVENTS_PY)
	@$(PYTHON) $(EVENTS_PY)

clean:
	@rm -rf $(SITE_DIR)

clean_all: clean
	@rm -f $(EVENTS_JSON)

serve: build
	@$(PYTHON) -m http.server -d $(SITE_DIR)

build_pages: $(STATIC_DIR)/*.html $(STATIC_DIR)/nav.html build_pages.py
	@mkdir -p $(SITE_DIR)
	@$(PYTHON) build_pages.py $(STATIC_DIR) $(SITE_DIR)

# events.json (+ Backup/Staging-Dateien) werden nur vom nightly-Job gepflegt und
# dürfen vom Deploy weder überschrieben noch per --delete entfernt werden.
# Nur beim Erst-Deploy (events.json fehlt im Webroot) wird sie initial kopiert.
deploy: build
	@sudo rsync -avh --delete \
		--exclude /events.json \
		--exclude /events.json.last-good \
		--exclude '/.events.json.tmp.*' \
		$(SITE_DIR)/ $(DEPLOY_DIR)/
	@if ! sudo test -f $(DEPLOY_DIR)/$(EVENTS_JSON); then \
		echo "Erst-Deploy: kopiere $(EVENTS_JSON) nach $(DEPLOY_DIR)"; \
		sudo install -m 0644 $(SITE_DIR)/$(EVENTS_JSON) $(DEPLOY_DIR)/$(EVENTS_JSON); \
	fi

nightly:
	@bash $(NIGHTLY_SCRIPT)
