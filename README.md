# Costituzione italiana — testo, revisioni, giurisprudenza e citazioni

**139 articoli, 22.389 pronunce, 266.811 massime, 15.969 citazioni. La Costituzione italiana come non l'hai mai vista: interrogabile.**

La Costituzione italiana ha 139 articoli. Alcuni sono famosi (Art. 21, libertà di stampa),
altri dimenticati (Art. 46, collaborazione dei lavoratori). Alcuni vengono invocati in
continuazione nei processi, altri mai.

Questo repo mette insieme **7 dataset** (+ 1 compose) per rispondere a domande come:
- *Quali relatori hanno più sentenze con esito "illegittimo"?*
- *L'Art. 3 (uguaglianza) è il più evocato in giudizio: ma quante volte viene accolto?*
- *I giudici eletti dal Senato relazionano su articoli diversi da quelli eletti dalla Camera?*

## Cosa contiene

| Dataset | Cosa | Quantità |
|---|---|---|
| **Articoli** | Ogni articolo con heading, parte, titolo, sezione | 157 righe |
| **Revisioni** | Leggi di revisione costituzionale (1948-2023) | 50 leggi |
| **Atti di promovimento** | Parametri costituzionali evocati in giudizio | 1.006 parametri |
| **Massime** | Esiti della Corte Costituzionale (1956-2026) | 266.811 massime |
| **Pronunce** | Pronunce con presidente, relatore, collegio, testo | 22.389 pronunce |
| **Giudici** | Anagrafica giudici costituzionali (eletto_da, date) | ~200 giudici |
| **Citazioni** | La Costituzione nella legislazione ordinaria | 15.969 citazioni |
| **Sentenze Complete** | Compose: pronunce × massime × giudici | 267.635 righe |

## Esempi di domande

- **Quali relatori hanno il tasso più alto di accoglimento?**
- **Quali articoli vengono citati nelle leggi ma mai portati davanti alla Corte?**
- **Come varia il tasso di accoglimento per articolo nel tempo?**
- **Quali giudici hanno relazionato su più sentenze illegittime?**

## Quick start

```bash
# Esegui tutti i dataset + compose
make run-all

# Esegui un singolo dataset
make run-massime

# Valid tutti i config
make check

# Genera registry
make registry-write
```

## Accedere ai dati

### 1. Via MCP (toolkit)

I 7 dataset sono accessibili via SQL dal server MCP toolkit del Lab.

### 2. Via DuckDB diretto

```sql
-- Relatori con più sentenze illegittime
SELECT relatore_pronuncia, n_illegittime, pct_illegittime
FROM 'out/data/mart/sentenze_complete/2026/mart_relatore_esiti.parquet'
ORDER BY n_illegittime DESC LIMIT 10;

-- Tasso di accoglimento per articolo
SELECT parametro_articolo, n_accolte, pct_accoglimento
FROM 'out/data/mart/sentenze_complete/2026/mart_sentenze_per_articolo.parquet'
ORDER BY n_accolte DESC LIMIT 10;
```

### 3. Via download parquet

I clean parquet sono in `out/data/clean/`, i mart in `out/data/mart/`.

## Dashboard Streamlit

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

## Architettura

```
costituzione-italiana/
├── datasets/                          ← 7 dataset (toolkit pipeline)
│   ├── articoli/
│   ├── revisioni/
│   ├── atti-promovimento/
│   ├── massime/
│   ├── pronunce/
│   ├── giudici/
│   ├── citazioni-legislative/
│   └── scripts/                       ← script di import
├── compose/
│   └── sentenze-complete/             ← cross-dataset (pronunce × massime × giudici)
├── dashboard/                         ← Streamlit
├── out/                               ← output pipeline (raw/clean/mart)
├── registry/                          ← artifact catalog
├── Makefile
└── pyproject.toml
```

## Fonti

| Dataset | Fonte | Licenza |
|---|---|---|
| Articoli | Wikisource | CC BY-SA 3.0 |
| Revisioni | italia-corpus via Normattiva | — |
| Atti di promovimento | dati.cortecostituzionale.it | CC BY-SA 3.0 |
| Massime | dati.cortecostituzionale.it | CC BY-SA 3.0 |
| Pronunce | dati.cortecostituzionale.it | CC BY-SA 3.0 |
| Giudici | dati.cortecostituzionale.it | CC BY-SA 3.0 |
| Citazioni | italia-corpus | — |

## Approfondimenti

- [Discussion: Come decide la Consulta?](https://github.com/orgs/dataciviclab/discussions/288)
- [Annuncio: costituzione_master — nuovo dataset pubblicato](https://github.com/dataciviclab/dataciviclab/issues/369)

## Licenza

- **Testo**: CC BY-SA 3.0 (da Wikisource)
- **Dati Corte Costituzionale**: CC BY-SA 3.0
- **Codice**: MIT
