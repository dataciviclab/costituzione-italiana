# Costituzione italiana — testo, revisioni, giurisprudenza e citazioni

[![check](https://github.com/dataciviclab/costituzione-italiana/actions/workflows/check.yml/badge.svg)](https://github.com/dataciviclab/costituzione-italiana/actions/workflows/check.yml)

**139 articoli, 22.428 pronunce, 46.665 massime, 16.174 citazioni.** La
Costituzione italiana e la giurisprudenza costituzionale in formato aperto e
interrogabile.

La Costituzione ha 139 articoli. Alcuni sono famosi (Art. 21, libertà di
stampa), altri dimenticati (Art. 46, collaborazione dei lavoratori). Alcuni
vengono invocati continuamente davanti alla Corte, altri mai.

Questo repo mette insieme **7 dataset + 2 compose** per rispondere a domande
come:

- *Quali relatori hanno più sentenze con esito "illegittimo"?*
- *L'Art. 3 (uguaglianza) è il più evocato: ma quante volte viene accolto?*
- *Quali articoli sono citati nelle leggi ma mai davanti alla Corte?*
- *Quante proposte di revisione costituzionale arrivano a legge?*

## Cosa contiene

| Dataset | Cosa | Quantità |
|---|---|---|
| **Articoli** | Ogni articolo con heading, parte, titolo, sezione | 139 articoli + 18 disposizioni |
| **Revisioni** | Leggi costituzionali (1947-2026) | 50 leggi |
| **Pronunce** | Presidente, relatore, collegio, epigrafe, testo integrale | 22.428 pronunce (1956-2026) |
| **Massime** | Esiti e parametri evocati, una riga per massima | 46.665 massime |
| **Giudici** | Anagrafica (eletto_da, date, nota biografica) | 136 voci |
| **Citazioni** | La Costituzione nelle collezioni di italia-corpus | 16.174 occorrenze |
| **Atti pendenti** | Parametri evocati nei giudizi ancora pendenti | 993 parametri (2024-2026) |
| **Sentenze Complete** | Compose: pronunce × massime × giudici | 46.718 righe |
| **Iter Costituzionale** | Compose: DDL Camera/Senato × revisioni | 2.737 proposte |

## Come accedere

### 1. Via MCP del Lab (`dcl-mcp`)

```text
find("massime corte costituzionale")      # trova il dataset
explore("massime_corte_costituzionale")   # card, colonne, mart, path GCS
gcs_query(slug="massime_corte_costituzionale",
          sql="SELECT esito, count(*) AS n FROM _data GROUP BY 1")
```

### 2. Via DuckDB, direttamente da GCS

```sql
-- Tasso di accoglimento per articolo (dai parametri delle massime)
SELECT parametro_articolo, n_casi, pct_accoglimento
FROM 'https://storage.googleapis.com/dataciviclab-mart/costituzione-italiana/sentenze_complete/2026/mart_sentenze_per_articolo.parquet'
ORDER BY n_casi DESC LIMIT 10;

-- Massime di una pronuncia
SELECT id_massima, esito, parametri
FROM 'https://storage.googleapis.com/dataciviclab-clean/costituzione-italiana/massime_corte_costituzionale/2026/massime_corte_costituzionale_2026_clean.parquet'
WHERE anno_pronuncia = 2026 AND numero_pronuncia = 192;
```

### 3. Dashboard

<https://dcl-costituzione-italiana.streamlit.app/>

## Sviluppo

```bash
pip install -e ".[dev,pipeline]"
make check        # preflight di tutti i dataset.yml
make run-all      # pipeline completa (dataset + compose)
make test         # contract, policy e smoke test
make registry     # dry-run del registry
```

Contribuzione e regole repo: [CONTRIBUTING.md](CONTRIBUTING.md).

## Architettura

```
datasets/                 ← 7 dataset (toolkit: raw → clean → mart)
compose/                  ← sentenze-complete, iter-costituzionale
dashboard/                ← Streamlit (GCS via lab-connectors)
registry/                 ← artifact registry (generato dalla pipeline)
tests/                    ← contract, policy, adapter
Costituzione.md           ← testo sorgente (Wikisource)
```

`massime` ha una riga per massima: `parametri` e `norme` sono due liste
indipendenti, conservate in JSON nel clean ed esplose nei mart
`mart_massime_parametri` e `mart_massime_norme`. Grain, chiavi e contratti
per i consumer: [docs/dati.md](docs/dati.md).

## Fonti e limiti

| Dataset | Fonte | Licenza |
|---|---|---|
| Articoli | Wikisource | CC BY-SA 3.0 |
| Revisioni, Citazioni | italia-corpus (Normattiva) | — |
| Pronunce, Massime, Giudici, Atti | dati.cortecostituzionale.it | CC BY-SA 3.0 |
| Codice | MIT | — |

- **Atti pendenti**: la fonte open data pubblica solo i registri dei giudizi
  pendenti (2024-2026), non la serie storica degli atti di promovimento.
- **Revisioni**: la fonte è la collezione "Leggi costituzionali"; include 3
  leggi pre-costituzionali del 1947, non solo revisioni del testo vigente.
- **Citazioni**: coperte le 19 collezioni di italia-corpus (4.771 atti), non
  tutte le leggi ordinarie.
- **Esito**: è derivato dal testo della massima, non un campo della fonte;
  circa un terzo delle massime resta `altro` (non classificato).
- **Giudici**: 136 voci come nell'anagrafica ufficiale, incluse 11 voci
  collettive presenti a monte.
- **Pronunce**: testo integrale disponibile per 12.196 pronunce (54,4%);
  `collegio` ed `epigrafe` per tutte.

## Partecipa

- Domande e segnalazioni: [GitHub Discussions](https://github.com/dataciviclab/dataciviclab/discussions)
- Bug e proposte: [issue del repo](https://github.com/dataciviclab/costituzione-italiana/issues)
- Come contribuire: [CONTRIBUTING.md](CONTRIBUTING.md)
