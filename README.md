# Costituzione della Repubblica Italiana

**Il testo vigente della Costituzione italiana, articolo per articolo, in formato queryabile.**

| | |
|---|---|
| Articoli | **139** |
| Disposizioni transitorie | **18** (I–XVIII) |
| Commi | **425** |
| Partizioni | 4 Parti · 10 Titoli · 9 Sezioni |
| Ultimo aggiornamento | L.cost. 26 settembre 2023, n. 1 (art. 33, sport) |
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
| `articoli.csv` | CSV | Una riga per articolo/disposizione |
| `articoli.parquet` | Parquet | Stesso contenuto in formato colonnare |

Schema articoli (31 campi):

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
-- Quanti commi ha ogni parte?
SELECT parte, SUM(commi) AS commi
FROM 'data/articoli.parquet'
GROUP BY parte ORDER BY commi DESC;

-- Articoli del Titolo V (Regioni)
SELECT articolo, heading
FROM 'data/articoli.parquet'
WHERE titolo LIKE '%Regioni%' OR titolo LIKE '%regioni%';

-- Testo dell'Art. 32
SELECT testo FROM 'data/articoli.parquet' WHERE articolo = 32;
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
│   ├── articoli.csv                    ← dataset per articolo
│   └── articoli.parquet
├── strumenti/
│   ├── converti-da-wikisource.py       ← Wikisource → Markdown
│   └── estrai-articoli.py              ← Markdown → CSV/parquet
├── tests/test_converti.py              ← 5 test
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

# Test
python3 -m pytest tests/ -v
```

## Schema del dataset (`dataset.yml`)

Vedi [`dataset.yml`](dataset.yml) per la definizione completa dei campi, coverage e metriche.

## Prossimi sviluppi

Vedi la [nota di piano](https://github.com/dataciviclab/costituzione-italiana/blob/main/...).

- **Fase 2**: collegamento con `italia-corpus` (leggi costituzionali di revisione)
- **Fase 3**: dati Corte Costituzionale (norme impugnate → parametri costituzionali)
- **Fase 4**: mappa articolo ↔ dataset DataCivicLab
- **Fase 5**: MCP server per ricerca full-text

## Licenza

- **Testo** della Costituzione: [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/) (da Wikisource)
- **Codice** del progetto: MIT
