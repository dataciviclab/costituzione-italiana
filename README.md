# Costituzione della Repubblica Italiana

**Il testo vigente della Costituzione italiana, le sue revisioni, la giurisprudenza costituzionale e gli indicatori di attuazione — tutto in formato queryabile.**

| | |
|---|---|
| Articoli | **139** |
| Disposizioni transitorie | **18** (I–XVIII) |
| Commi | **425** |
| Partizioni | 4 Parti · 10 Titoli · 9 Sezioni |
| Leggi di revisione | **50** (di cui **20** modificano articoli della Costituzione) |
| Parametri costituzionali in giudizio | **1.101** (da 886 ordinanze + 215 ricorsi) |
| Indicatori di attuazione | **38** per 17 articoli |
| Ultimo aggiornamento testo | L.cost. 26 settembre 2023, n. 1 (art. 33, sport) |
| Licenza | CC BY-SA 3.0 (testo) / MIT (codice) |

---

## Dataset

### 1. `Costituzione.md` — Testo vigente

Il testo completo in Markdown con YAML frontmatter, seguendo lo standard di [`italia-corpus`](https://github.com/dataciviclab/italia-corpus):

```markdown
---
tipo: COSTITUZIONE
numero: 1
data: 1947-12-27
titolo: "Costituzione della Repubblica Italiana"
urn: urn:nir:stato:costituzione:1947-12-27
codice_redazionale: 047U0001
vigente: true
---

# Principi fondamentali
## Art. 1
L'Italia è una Repubblica democratica, fondata sul lavoro.
...
```

**Fonte**: [Wikisource](https://it.wikisource.org/wiki/Italia,_Repubblica_-_Costituzione) (CC BY-SA 3.0),
allineato con il testo vigente su [Normattiva](https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:costituzione:1947-12-27).

### 2. `data/articoli.parquet` — Articoli strutturati

Ogni articolo/disposizione è una riga, con 8 campi.

```sql
-- Testo dell'Art. 32 (diritto alla salute)
SELECT testo FROM 'data/articoli.parquet' WHERE articolo = 32;

-- Quanti commi ha ogni parte?
SELECT parte, SUM(commi) AS commi
FROM 'data/articoli.parquet'
GROUP BY parte ORDER BY commi DESC;

-- Articoli del Titolo V (Regioni)
SELECT articolo, heading
FROM 'data/articoli.parquet'
WHERE titolo LIKE '%Regioni%';
```

### 3. `data/revisioni.parquet` — Leggi di revisione costituzionale

50 leggi costituzionali da [`italia-corpus`](https://github.com/dataciviclab/italia-corpus),
classificate in 20 modifiche alla Costituzione, 17 statuti speciali, 13 altre.
Per ogni modifica, gli articoli della Costituzione modificati.

```sql
-- Quali leggi hanno modificato l'art. 9 (ambiente)?
SELECT data, titolo
FROM 'data/revisioni.parquet'
WHERE list_has_any(articoli_modificati, [9]);

-- Quali articoli sono stati modificati più volte?
SELECT art, COUNT(*) AS volte
FROM 'data/revisioni.parquet', LATERAL UNNEST(articoli_modificati) AS t(art)
WHERE tipo = 'modifica_costituzione'
GROUP BY art ORDER BY volte DESC;
```

### 4. `data/atti-promovimento.parquet` — Giurisprudenza costituzionale

1.101 parametri costituzionali evocati nei giudizi di legittimità costituzionale,
estratti dall'XML pubblicato giornalmente su [dati.cortecostituzionale.it](https://dati.cortecostituzionale.it)
(CC BY-SA 3.0). Ogni record collega una norma impugnata all'articolo della
Costituzione evocato come parametro.

**Top 10 articoli più evocati in giudizio:**

| Articolo | Volte |
|---|---|
| Art. 3 (uguaglianza) | 213 |
| Art. 117 (competenze Stato-Regioni) | 187 |
| Art. 24 (diritto di difesa) | 69 |
| Art. 111 (giusto processo) | 64 |
| Art. 97 (buon andamento PA) | 49 |
| Art. 77 (decreti-legge) | 43 |
| Art. 27 (finalità rieducativa pena) | 42 |
| Art. 25 (riserva di legge) | 39 |
| Art. 11 (diritto internazionale) | 38 |
| Art. 102 (giudice naturale) | 27 |

```sql
-- Quali sono gli articoli più evocati?
SELECT parametro_articolo, COUNT(*) AS volte
FROM 'data/atti-promovimento.parquet'
GROUP BY parametro_articolo ORDER BY volte DESC;

-- Art. 32 (salute) in giudizio
SELECT anno, norma_descrizione, norme_str
FROM 'data/atti-promovimento.parquet'
WHERE parametro_articolo = 32;
```

### 5. `data/indicatori-costituzionali.parquet` — Mappa con i dataset Lab

38 indicatori che collegano 17 articoli della Costituzione ai dataset del
[DataCivicLab](https://github.com/dataciviclab). Ogni riga collega un articolo
a uno slug del [clean_catalog](https://github.com/dataciviclab/dataset-incubator/blob/main/registry/clean_catalog.json).

| Articolo | Dimensione | Dataset Lab |
|---|---|---|
| Art. 9 | Ambiente | Terna (rinnovabili, mix), ISPRA (rifiuti, suolo, emissioni) |
| Art. 32 | Salute | BDAP LEA, AIFA, strutture ASL, farmacie |
| Art. 41 | Impresa | ANAC bandi, RNA aiuti di Stato |
| Art. 53 | Fisco | IRPEF comunale, Gini regionale |
| Art. 97 | Buona PA | Dipendenti pubblici, ANAC, Consip |
| Art. 111 | Giustizia | Flussi civili, indicatori penali |

```sql
-- Quali dataset misurano l'art. 9?
SELECT dataset_name, dimensione
FROM 'data/indicatori-costituzionali.parquet'
WHERE articolo = 9;

-- Quali articoli hanno più indicatori?
SELECT articolo, COUNT(*) AS n
FROM 'data/indicatori-costituzionali.parquet'
GROUP BY articolo ORDER BY n DESC;
```

### Analisi incrociata

I 5 dataset si combinano per rispondere a domande come:

```sql
-- Art. 9: testo, modifiche, giudizi, indicatori
SELECT 'Art. 9 — Tutela ambiente' AS articolo,
    (SELECT COUNT(*) FROM 'data/revisioni.parquet'
     WHERE list_has_any(articoli_modificati, [9])) AS modifiche,
    (SELECT COUNT(*) FROM 'data/atti-promovimento.parquet'
     WHERE parametro_articolo = 9) AS giudizi,
    (SELECT COUNT(*) FROM 'data/indicatori-costituzionali.parquet'
     WHERE articolo = 9) AS indicatori;
```

## Architettura

```
costituzione-italiana/
├── Costituzione.md                        ← testo vigente (139 art. + 18 disp.)
├── data/
│   ├── articoli.csv / .parquet            ← 157 righe, 8 campi
│   ├── revisioni.csv / .parquet           ← 50 leggi, 7 campi
│   ├── atti-promovimento.csv / .parquet   ← 1.101 parametri, 11 campi
│   └── indicatori-costituzionali.csv/.parquet ← 38 indicatori, 6 campi
├── strumenti/
│   ├── converti-da-wikisource.py          ← Wikisource → Costituzione.md
│   ├── estrai-articoli.py                 ← Costituzione.md → articoli.parquet
│   ├── importa-revisioni.py              ← italia-corpus → revisioni.parquet
│   ├── importa-corte-costituzionale.py    ← Corte XML → atti-promovimento.parquet
│   └── genera-indicatori-costituzionali.py ← clean_catalog → indicatori.parquet
├── tests/
│   └── test_converti.py                   ← 12 test
├── dataset.yml                            ← metadati DataCivicLab
└── pyproject.toml                         ← pacchetto Python
```

### Riprodurre

```bash
pip install -e ".[dev]"

# Test
python3 -m pytest tests/ -v

# Rigenerare Costituzione.md da Wikisource
python3 strumenti/converti-da-wikisource.py

# Rigenerare dataset derivati
python3 strumenti/estrai-articoli.py
python3 strumenti/importa-revisioni.py          # richiede italia-corpus
python3 strumenti/importa-corte-costituzionale.py
python3 strumenti/genera-indicatori-costituzionali.py  # richiede dataset-incubator
```

## Fonti

| Dataset | Fonte | Licenza |
|---|---|---|
| Testo della Costituzione | [Wikisource](https://it.wikisource.org/wiki/Italia,_Repubblica_-_Costituzione) | CC BY-SA 3.0 |
| Leggi di revisione | [italia-corpus](https://github.com/dataciviclab/italia-corpus) via Normattiva | — |
| Atti di promovimento | [dati.cortecostituzionale.it](https://dati.cortecostituzionale.it) | CC BY-SA 3.0 |
| Dataset Lab | [clean_catalog](https://github.com/dataciviclab/dataset-incubator/blob/main/registry/clean_catalog.json) | Varie |

## Schema del dataset (`dataset.yml`)

Vedi [`dataset.yml`](dataset.yml) per la definizione completa dei campi,
coverage e metriche di tutti e 4 i dataset.

## Licenza

- **Testo** della Costituzione: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) (da Wikisource)
- **Dati** della Corte Costituzionale: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)
- **Codice** del progetto: MIT
