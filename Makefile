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
.PHONY: $(addprefix run-,$(notdir $(dir $(DATASETS))))
$(addprefix run-,$(notdir $(dir $(DATASETS)))):
	@slug=$@; slug=$${slug#run-}; \
	config=$$(find datasets -maxdepth 2 -name dataset.yml -path "*/$$slug/*" | head -1); \
	if [ -z "$$config" ]; then echo "❌ Dataset '$$slug' non trovato"; exit 1; fi; \
	echo "=== $$slug ==="; \
	$(TOOLKIT) run --config "$$config"

# --- Compose (dopo i dataset) ------------------------------------------------

.PHONY: compose
compose:
	@for f in $(COMPOSE); do \
		echo "=== $$f (compose) ==="; \
		$(TOOLKIT) run --config "$$f" || exit 1; \
	done

.PHONY: $(addprefix run-,$(notdir $(dir $(COMPOSE))))
$(addprefix run-,$(notdir $(dir $(COMPOSE)))):
	@slug=$@; slug=$${slug#run-}; \
	config=$$(find compose -maxdepth 2 -name dataset.yml -path "*/$$slug/*" | head -1); \
	if [ -z "$$config" ]; then echo "❌ Compose '$$slug' non trovato"; exit 1; fi; \
	echo "=== $$slug (compose) ==="; \
	$(TOOLKIT) run --config "$$config"

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

.PHONY: $(addprefix status-,$(notdir $(dir $(DATASETS))) $(addprefix status-,$(notdir $(dir $(COMPOSE)))))
$(addprefix status-,$(notdir $(dir $(DATASETS))) $(addprefix status-,$(notdir $(dir $(COMPOSE))))):
	@slug=$@; slug=$${slug#status-}; \
	config=$$(find datasets compose -maxdepth 2 -name dataset.yml -path "*/$$slug/*" | head -1); \
	$(TOOLKIT) inspect summary --config "$$config" 2>/dev/null || echo "Nessuno stato per $$slug"

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
