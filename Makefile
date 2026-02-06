SITE_DIR := _site
STATIC_DIR := static
EVENTS_JSON := events.json
EVENTS_PY := events.py
PYTHON := python3
DEPLOY_DIR ?= /etc/nginx/sites-available/ohmoors
NIGHTLY_SCRIPT := scripts/nightly_update.sh

.PHONY: all build copy_static copy_events_json clean serve deploy nightly update_events

all: build

build: copy_static copy_events_json build_pages

jesus: clean build

love: build serve

it_so: clean_all build serve

copy_static:
	@mkdir -p $(SITE_DIR)
	@cp -a $(STATIC_DIR)/. $(SITE_DIR)/

copy_events_json: $(EVENTS_JSON)
	@mkdir -p $(SITE_DIR)
	@cp $(EVENTS_JSON) $(SITE_DIR)/$(EVENTS_JSON)

update_events:
	@$(PYTHON) $(EVENTS_PY)

$(EVENTS_JSON): $(EVENTS_PY)
	@$(PYTHON) $(EVENTS_PY)

clean:
	@rm -rf $(SITE_DIR)

clean_all: clean
	@rm $(EVENTS_JSON)

serve: build
	@$(PYTHON) -m http.server -d $(SITE_DIR)

build_pages: $(STATIC_DIR)/*.html $(STATIC_DIR)/nav.html build_pages.py
	@mkdir -p $(SITE_DIR)
	@$(PYTHON) build_pages.py $(STATIC_DIR) $(SITE_DIR)

deploy: build
	@rsync -a --delete $(SITE_DIR)/ $(DEPLOY_DIR)/

nightly:
	@bash $(NIGHTLY_SCRIPT)
