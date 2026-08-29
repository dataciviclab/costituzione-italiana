# Costituzione italiana — testo, revisioni, giurisprudenza e citazioni

**139 articoli, 21.534 sentenze, 15.969 citazioni nella legislazione. La Costituzione italiana come non l'hai mai vista: interrogabile.**

La Costituzione italiana ha 139 articoli. Alcuni sono famosi (Art. 21, libertà di stampa),
altri dimenticati (Art. 46, collaborazione dei lavoratori). Alcuni vengono invocati in
continuazione nei processi, altri mai.

Questo repo mette insieme **6 dataset** per rispondere a domande come:
- *L'Art. 3 (uguaglianza) è il più evocato in giudizio: ma quante volte le leggi vengono
  effettivamente dichiarate incostituzionali?* (2.816 accolte, 5.202 respinte)
- *L'Art. 76 (delega legislativa) è citato 5.744 volte nella legislazione ordinaria.*
- *Quali articoli vengono citati nelle leggi ma mai portati davanti alla Corte?*

## Cosa contiene

| Dataset | Cosa | Quantità |
|---|---|---|
| **Testo** | Costituzione.md (139 art. + 18 disposizioni) | 425 commi |
| **Articoli** | Ogni articolo con heading e partizione | 157 righe |
| **Revisioni** | Leggi di revisione costituzionale (1948-2023) | 50 leggi |
| **Giurisprudenza** | Parametri costituzionali evocati in giudizio | 1.006 parametri |
| **Massime** | Esiti della Corte Costituzionale (1956-2026) | 266.770 massime |
| **Citazioni** | La Costituzione nella legislazione ordinaria | 15.969 citazioni |

## Esempi di domande

- **Quali articoli della Costituzione sono stati modificati più volte?**
- **L'Art. 9 (ambiente) è stato invocato in giudizio? Con che esito?**
- **Quali leggi ordinarie citano l'Art. 117 (competenze Stato-Regioni)?**
- **Quali articoli hanno il più alto tasso di accoglimento in Corte Costituzionale?**

## Tre modi per accedere ai dati

### 1. Via MCP (toolkit)

I 6 dataset sono accessibili via SQL dal server MCP toolkit del Lab.

```
"Quali articoli sono stati accolti più spesso dalla Corte?"
"Quante volte l'Art. 21 è stato citato nella legislazione?"
```

### 2. Via DuckDB diretto

```sql
-- Articolo più evocato in giudizio
SELECT parametro_articolo, COUNT(*) AS volte
FROM 'data/atti-promovimento.parquet'
GROUP BY parametro_articolo ORDER BY volte DESC;

-- Tasso di accoglimento per articolo
SELECT parametro_articolo,
    SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) AS pct
FROM 'data/massime.parquet'
GROUP BY parametro_articolo HAVING COUNT(*) > 50
ORDER BY pct DESC;
```

### 3. Via download parquet

Tutti i dataset sono in `data/` nel repo.

## Dashboard Streamlit

Una dashboard interattiva è disponibile nella cartella `dashboard/`:

```bash
pip install -r dashboard/requirements.txt
streamlit run dashboard/app.py
```

## Approfondimenti

- [Discussion: Come decide la Consulta?](https://github.com/orgs/dataciviclab/discussions/288)
- [Annuncio: costituzione_master — nuovo dataset pubblicato](https://github.com/dataciviclab/dataciviclab/issues/369)

## Architettura

```
costituzione-italiana/
├── Costituzione.md                     ← testo vigente
├── data/                               ← 6 dataset in parquet + CSV
├── dashboard/                          ← dashboard Streamlit interattiva
├── strumenti/                          ← script di import/export
├── tests/                              ← test
├── dataset.yml
└── pyproject.toml
```

## Fonti

| Dataset | Fonte | Licenza |
|---|---|---|
| Testo della Costituzione | Wikisource | CC BY-SA 3.0 |
| Leggi di revisione | italia-corpus via Normattiva | — |
| Atti di promovimento | dati.cortecostituzionale.it | CC BY-SA 3.0 |
| Massime | dati.cortecostituzionale.it | CC BY-SA 3.0 |
| Citazioni legislative | italia-corpus | — |

## Licenza

- **Testo**: CC BY-SA 3.0 (da Wikisource)
- **Dati Corte Costituzionale**: CC BY-SA 3.0
- **Codice**: MIT
