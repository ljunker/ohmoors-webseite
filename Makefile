SITE_DIR := _site
STATIC_DIR := static
EVENTS_JSON := events.json
EVENTS_PY := events.py
SCHEDULE_HTML := $(SITE_DIR)/schedule.html
PYTHON := python3

.PHONY: all build copy_static clean serve

all: build

build: copy_static build_pages $(SCHEDULE_HTML)

copy_static:
	@mkdir -p $(SITE_DIR)
	@cp -a $(STATIC_DIR)/. $(SITE_DIR)/

$(SCHEDULE_HTML): $(EVENTS_JSON) $(STATIC_DIR)/nav.html generate_schedule.py
	@mkdir -p $(SITE_DIR)
	@$(PYTHON) generate_schedule.py $(EVENTS_JSON) $(STATIC_DIR)/nav.html $(SCHEDULE_HTML)

$(EVENTS_JSON): $(EVENTS_PY)
	@$(PYTHON) $(EVENTS_PY)

clean:
	@rm -rf $(SITE_DIR)
	@rm $(EVENTS_JSON)

serve: build
	@$(PYTHON) -m http.server -d $(SITE_DIR)
build_pages: $(STATIC_DIR)/*.html $(STATIC_DIR)/nav.html build_pages.py
	@mkdir -p $(SITE_DIR)
	@$(PYTHON) build_pages.py $(STATIC_DIR) $(SITE_DIR)
