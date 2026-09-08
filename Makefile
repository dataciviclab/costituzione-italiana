TOOLKIT = toolkit

# ─── Datasets (ordine libero, nessuna dipendenza tra loro) ─────
DATASETS = \
	datasets/articoli \
	datasets/revisioni \
	datasets/atti-promovimento \
	datasets/massime \
	datasets/citazioni-legislative \
	datasets/pronunce \
	datasets/giudici

# ─── Compose (dipendono dai clean dei datasets) ───────────────
COMPOSE = \
	compose/sentenze-complete

# ─── Run singolo dataset ──────────────────────────────────────
.PHONY: $(addprefix run-,$(notdir $(DATASETS))) $(addprefix run-,$(notdir $(COMPOSE)))

$(addprefix run-,$(notdir $(DATASETS))):
	@slug=$@; slug=$${slug#run-}; \
	config=$$(find datasets -maxdepth 2 -name dataset.yml -path "*/$$slug/*" | head -1); \
	if [ -z "$$config" ]; then echo "❌ Dataset '$$slug' non trovato"; exit 1; fi; \
	echo "=== $$slug ==="; \
	$(TOOLKIT) run --config "$$config"

$(addprefix run-,$(notdir $(COMPOSE))):
	@slug=$@; slug=$${slug#run-}; \
	config=$$(find compose -maxdepth 2 -name dataset.yml -path "*/$$slug/*" | head -1); \
	if [ -z "$$config" ]; then echo "❌ Compose '$$slug' non trovato"; exit 1; fi; \
	echo "=== $$slug (compose) ==="; \
	$(TOOLKIT) run --config "$$config"

# ─── Run all: datasets prima, compose dopo ────────────────────
.PHONY: run-datasets run-compose run-all
run-datasets:
	@for d in $(DATASETS); do \
		echo "=== $$d ==="; \
		$(TOOLKIT) run --config $$d/dataset.yml || exit 1; \
	done

run-compose: run-datasets
	@for d in $(COMPOSE); do \
		echo "=== $$d (compose) ==="; \
		$(TOOLKIT) run --config $$d/dataset.yml || exit 1; \
	done

run-all: run-compose

# ─── Preflight: valida tutti i config ─────────────────────────
.PHONY: check
check:
	@for f in $$(find datasets compose -name dataset.yml | sort); do \
		echo "→ $$f"; \
		$(TOOLKIT) run preflight --config "$$f" > /dev/null 2>&1 || exit 1; \
	done
	@echo "✅ All configs valid"

# ─── Status singolo dataset ───────────────────────────────────
.PHONY: $(addprefix status-,$(notdir $(DATASETS))) $(addprefix status-,$(notdir $(COMPOSE)))

$(addprefix status-,$(notdir $(DATASETS))):
	@slug=$@; slug=$${slug#status-}; \
	config=$$(find datasets -maxdepth 2 -name dataset.yml -path "*/$$slug/*" | head -1); \
	$(TOOLKIT) inspect summary --config "$$config" 2>/dev/null || echo "Nessuno stato per $$slug"

$(addprefix status-,$(notdir $(COMPOSE))):
	@slug=$@; slug=$${slug#status-}; \
	config=$$(find compose -maxdepth 2 -name dataset.yml -path "*/$$slug/*" | head -1); \
	$(TOOLKIT) inspect summary --config "$$config" 2>/dev/null || echo "Nessuno stato per $$slug"

# ─── Registry ─────────────────────────────────────────────────
.PHONY: registry registry-write
registry:
	$(TOOLKIT) registry build --prefix costituzione-italiana

registry-write:
	$(TOOLKIT) registry build --prefix costituzione-italiana --write

# ─── Pulizia ──────────────────────────────────────────────────
.PHONY: clean clean-runs
clean:
	rm -rf out/data/_runs out/data/raw out/data/clean out/data/mart

clean-runs:
	rm -rf out/data/_runs/

# ─── Help ─────────────────────────────────────────────────────
.PHONY: help
help:
	@grep -E '^[a-zA-Z_-]+:' Makefile | sort
