# Contributing — Costituzione italiana

Repo dataset multi-dataset: 7 dataset toolkit + 2 compose cross-dataset
(`sentenze-complete`, `iter-costituzionale`), dashboard Streamlit, registry.

## Setup

```bash
pip install -e ".[dev,pipeline,dashboard]"
```

Le dipendenze vivono in `pyproject.toml` (standard Lab).
`dashboard/requirements.txt` è solo export pin per Streamlit Cloud.

## Pipeline

```bash
make check            # preflight su tutti i dataset.yml + compose
make run              # tutti i dataset singoli
make run-massime      # un singolo dataset (alias)
make compose          # compose (dopo make run)
make run-all          # dataset + compose (come CI post-merge)
make test             # pytest su tests/ e dashboard/tests/
make dashboard        # Streamlit (richiede extra dashboard)
make registry-write   # scrivi registry.json
make clean            # pulisci output
```

`TOOLKIT_ALLOW_SCRIPT_SOURCE=1` è già esportato dal Makefile (script raw).

## Aggiungere un dataset

1. Crea `datasets/<slug>/dataset.yml` (schema `schema_version: 1`)
2. Se serve un extract: `datasets/scripts/<script>.py` (output `.parquet`, niente path host assoluti)
3. Crea `datasets/<slug>/sql/clean.sql` e `sql/mart/mart_*.sql`
4. `TOOLKIT_ALLOW_SCRIPT_SOURCE=1 toolkit run --config datasets/<slug>/dataset.yml`
5. Verifica con `make check` e `make test`
6. Se entra nel compose: aggiungilo in `compose/<slug>/dataset.yml` (support + clean.sql)
7. Aggiorna `registry/registry.json` (`make registry-write`) e il README
8. Aggiungi lo slug in `dashboard/sources.py` e una pagina se ha senso

## Aggiungere un compose

1. Crea `compose/<slug>/dataset.yml` — raw da clean di altri dataset (`local_file` o `type: dataset`)
2. Support esterni (es. open-politica) con `type: external` e URI `{year}` — mai path hardcoded
3. `clean.sql` solo da `raw_input` e `{support.*.outputs}` (placeholder toolkit)
4. Mart sintetici + `required_tables` + `table_rules`
5. Test policy in `tests/` sulle chiavi di join (vedi `tests/test_iter_costituzionale.py`)

## Regole

- Segui gli standard del Lab: `infra/lab-ops/standards/`
- `clean.sql` legge solo da `raw_input` (e placeholder support nel compose)
- `mart*.sql` legge solo da `clean_input`
- Ogni `mart*.sql` produce **1 tabella** dichiarata in `mart.tables`
- Nessun path assoluto da sviluppo locale nei `dataset.yml` (regression PR #23)
- Non committare output (`out/`, `*.parquet`, `*.csv` generati)
- Contratti cross-repo (slug, colonne, artifact registry) non si cambiano senza issue

## CI

- `check.yml` (PR + push main): ruff + pytest su `tests/` e `dashboard/tests/`; su PR con changed dataset/compose anche preflight config
- `pipeline.yml` (merge PR, schedule, dispatch): `make run-all` + registry PR

## Dashboard

- Data layer: API pubbliche `lab_connectors.duckdb.queries` (`load_clean`, `load_mart_table`)
- Branding obbligatorio: `lab_connectors.branding.apply_branding`
- Smoke test in `dashboard/tests/test_smoke.py`

## PR

Usa il template in `.github/PULL_REQUEST_TEMPLATE.md`.
Nessun merge senza autorizzazione umana.
