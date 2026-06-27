# Costituzione della Repubblica Italiana

**Il testo vigente della Costituzione italiana, articolo per articolo, in formato queryabile.**

| | |
|---|---|---|
| Articoli | **139** |
| Disposizioni transitorie | **18** (I–XVIII) |
| Commi | **425** |
| Partizioni | 4 Parti · 10 Titoli · 9 Sezioni |
| Ultimo aggiornamento | L.cost. 26 settembre 2023, n. 1 (art. 33, sport) |
| Leggi di revisione | **50** (da italia-corpus) di cui **24** modificano articoli della Costituzione |
| Licenza | CC BY-SA 3.0 (testo) / MIT (codice) |

## Cosa contiene

### `Costituzione.md`
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
fonte: https://it.wikisource.org/wiki/Italia,_Repubblica_-_Costituzione
licenza: CC BY-SA 3.0
---

# Principi fondamentali
## Art. 1
L'Italia è una Repubblica democratica, fondata sul lavoro.
...
```

### Dataset derivati (`data/`)
| File | Formato | Descrizione |
|---|---|---|
| `articoli.csv` / `.parquet` | CSV + Parquet | Una riga per articolo/disposizione (157 righe) |
| `revisioni.csv` / `.parquet` | CSV + Parquet | 50 leggi costituzionali di revisione |

**Schema articoli** (8 campi):
```
articolo             # numero (1–139) o null per disposizioni
disposizione         # numero romano (I–XVIII) o null per articoli
parte                # es. "Principi fondamentali"
titolo               # es. "Rapporti civili"
sezione              # es. "Le Camere"
heading              # es. "Art. 1", "Disposizione transitoria I"
testo                # testo completo
commi                # conteggio commi
```

**Schema revisioni** (7 campi):
```
urn                  # URN Normattiva della legge
codice_redazionale   # codice Gazzetta Ufficiale
data                 # data di emanazione
titolo               # titolo della legge
articoli_modificati  # lista articoli della Costituzione modificati
n_articoli           # quanti articoli modifica
tipo                 # modifica_costituzione / statuto_speciale / altra_legge_costituzionale
```

## Uso rapido

```bash
# Leggere il testo in Python
from pathlib import Path
contenuto = Path("Costituzione.md").read_text()

# Query CSV
python3 -c "
import csv
with open('data/articoli.csv') as f:
    for row in csv.DictReader(f):
        if row['parte'] == 'Principi fondamentali':
            print(f\"{row['heading']}: {row['testo'][:80]}...\")
"

# Esempio: articoli per parte
python3 -c "
import csv
from collections import Counter
with open('data/articoli.csv') as f:
    print(Counter(r['parte'] for r in csv.DictReader(f)))
"
```

### Query SQL con DuckDB

```sql
-- Testo dell'Art. 32
SELECT testo FROM 'data/articoli.parquet' WHERE articolo = 32;

-- Quanti commi ha ogni parte?
SELECT parte, SUM(commi) AS commi
FROM 'data/articoli.parquet'
GROUP BY parte ORDER BY commi DESC;

-- Quali leggi hanno modificato l'art. 9?
SELECT data, titolo
FROM 'data/revisioni.parquet'
WHERE list_has_any(articoli_modificati, [9]);

-- Quali articoli sono stati modificati più volte?
SELECT UNNEST(articoli_modificati) AS art, COUNT(*) AS volte
FROM 'data/revisioni.parquet'
WHERE tipo = 'modifica_costituzione'
GROUP BY art ORDER BY volte DESC;
```

## Fonte

Il testo proviene da [Wikisource](https://it.wikisource.org/wiki/Italia,_Repubblica_-_Costituzione) (CC BY-SA 3.0),
allineato con il testo vigente pubblicato su [Normattiva](https://www.normattiva.it/uri-res/N2Ls?urn:nir:stato:costituzione:1947-12-27).

Lo script [`converti-da-wikisource.py`](strumenti/converti-da-wikisource.py) scarica e converte automaticamente
il wikitext in Markdown strutturato, rimuovendo tag `<ref>`, template wiki e formattazione non standard.

## Architettura

```
costituzione-italiana/
├── Costituzione.md                     ← testo vigente
├── data/
│   ├── articoli.csv / .parquet         ← dataset per articolo
│   └── revisioni.csv / .parquet        ← leggi di revisione da italia-corpus
├── strumenti/
│   ├── converti-da-wikisource.py       ← Wikisource → Markdown
│   ├── estrai-articoli.py              ← Markdown → CSV/parquet
│   └── importa-revisioni.py           ← italia-corpus → revisioni CSV/parquet
├── tests/test_converti.py              ← 8 test
├── dataset.yml                         ← metadati DataCivicLab
└── pyproject.toml                      ← pacchetto Python
```

### Riprodurre

```bash
pip install -e ".[dev]"

# Rigenerare Costituzione.md da Wikisource (aggiorna il testo)
python3 strumenti/converti-da-wikisource.py

# Rigenerare dataset derivati
python3 strumenti/estrai-articoli.py
python3 strumenti/importa-revisioni.py   # richiede italia-corpus clonato

# Test
python3 -m pytest tests/ -v
```

## Schema del dataset (`dataset.yml`)

Vedi [`dataset.yml`](dataset.yml) per la definizione completa dei campi, coverage e metriche.

## Prossimi sviluppi

- **Fase 3**: dati Corte Costituzionale (norme impugnate → parametri costituzionali)
- **Fase 4**: mappa articolo ↔ dataset DataCivicLab
- **Fase 5**: MCP server per ricerca full-text

## Licenza

- **Testo** della Costituzione: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) (da Wikisource)
- **Codice** del progetto: MIT
