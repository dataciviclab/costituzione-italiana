# CLI toolkit del Lab. Le dipendenze runtime vivono in pyproject.toml:
#   pip install -e ".[dev,pipeline,dashboard]"
TOOLKIT = toolkit
export TOOLKIT_ALLOW_SCRIPT_SOURCE ?= 1

# Scoperta automatica dei config (nessuna lista hardcoded)
DATASETS := $(shell find datasets -name dataset.yml 2>/dev/null | sort)
COMPOSE  := $(shell find compose -name dataset.yml 2>/dev/null | sort)

# --- Dataset singoli ----------------------------------------------------------

.PHONY: run
run:
	@for f in $(DATASETS); do \
		echo "=== $$f ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done

# Alias documentato in README/CONTRIBUTING: make run-<slug>
# Pattern rule: `$(notdir $(dir ...))` espandeva a vuoto (trailing slash),
# quindi i target run-<slug> non esistevano.
run-%:
	@slug=$*; \
	config=$$(find datasets compose -maxdepth 2 -name dataset.yml -path "*/$$slug/dataset.yml" | head -1); \
	[ -n "$$config" ] || { echo "❌ Dataset '$$slug' non trovato"; exit 1; }; \
	echo "=== $$slug ==="; \
	$(TOOLKIT) run --config "$$config"

# --- Compose (dopo i dataset) ------------------------------------------------

.PHONY: compose
compose:
	@for f in $(COMPOSE); do \
		echo "=== $$f (compose) ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done

# CI post-merge e dispatch: dataset + compose
.PHONY: run-all
run-all: run compose

# Alias documentato
.PHONY: all
all: run-all test

# --- Preflight: valida tutti i config ----------------------------------------

.PHONY: check
check:
	@for f in $(DATASETS) $(COMPOSE); do \
		echo "-> $$f"; \
		$(TOOLKIT) run preflight --config "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

# --- Status singolo dataset/compose ------------------------------------------

status-%:
	@slug=$*; \
	config=$$(find datasets compose -maxdepth 2 -name dataset.yml -path "*/$$slug/dataset.yml" | head -1); \
	[ -n "$$config" ] || { echo "❌ Dataset '$$slug' non trovato"; exit 1; }; \
	$(TOOLKIT) inspect runs --config "$$config" 2>/dev/null || echo "Nessuno stato per $$slug"

# --- Registry (artifact catalogo — dry-run di default) -----------------------

.PHONY: registry registry-write
registry:
	$(TOOLKIT) registry build --prefix costituzione-italiana

registry-write:
	$(TOOLKIT) registry build --prefix costituzione-italiana --write

# --- Test --------------------------------------------------------------------

.PHONY: test
test:
	pytest tests/ dashboard/tests/ -v

# --- Dashboard ---------------------------------------------------------------
# Richiede: pip install -e ".[dashboard]"

.PHONY: dashboard
dashboard:
	cd dashboard && streamlit run app.py --server.headless=true

# --- Pulizia -----------------------------------------------------------------

.PHONY: clean clean-runs
clean:
	rm -rf out/data/_runs out/data/raw out/data/clean out/data/mart out/data/probe

clean-runs:
	rm -rf out/data/_runs/

# --- Help --------------------------------------------------------------------

.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
