# Costituzione italiana — testo, revisioni, giurisprudenza e attuazione

**139 articoli, 21.534 sentenze, 15.969 citazioni nella legislazione. La Costituzione italiana come non l'hai mai vista: interrogabile.**

La Costituzione italiana ha 139 articoli. Alcuni sono famosi (Art. 21, libertà di stampa),
altri dimenticati (Art. 46, collaborazione dei lavoratori). Alcuni vengono invocati in
continuazione nei processi, altri mai.

Questo repo mette insieme **7 dataset** per rispondere a domande come:
- *Quali articoli non hanno ancora una legge di attuazione?*
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
| **Giurisprudenza** | Parametri costituzionali evocati in giudizio | 1.101 parametri |
| **Massime** | Esiti della Corte Costituzionale (1956-2026) | 21.534 sentenze |
| **Citazioni** | La Costituzione nella legislazione ordinaria | 15.969 citazioni |
| **Indicatori** | 59 indicatori che collegano 21 articoli ai dataset del Lab | 59 mapping |

## Esempi di domande

- **Quali articoli della Costituzione sono stati modificati più volte?**
- **L'Art. 9 (ambiente) è stato invocato in giudizio? Con che esito?**
- **Quali leggi ordinarie citano l'Art. 117 (competenze Stato-Regioni)?**
- **Quali articoli hanno il più alto tasso di accoglimento in Corte Costituzionale?**
- **Quali dataset del Lab misurano l'attuazione dell'Art. 32 (salute)?**

## Tre modi per accedere ai dati

### 1. Via MCP (clean-query)

I 7 dataset sono accessibili via SQL dal server MCP clean-query del Lab.

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

## Approfondimenti

- [Discussion: Come decide la Consulta?](https://github.com/orgs/dataciviclab/discussions/288)
- [Annuncio: costituzione_master — nuovo dataset pubblicato](https://github.com/dataciviclab/dataciviclab/issues/369)

## Dataset in dettaglio

Ogni dataset ha la sua documentazione con schema e SQL nel resto di questo README.
Vedi: [dataset.yml](dataset.yml) per la definizione completa dei campi.

## Partecipa

- **Hai una domanda su questi dati?** Apri una [Discussion](https://github.com/orgs/dataciviclab/discussions/new?category=Domanda)
- **Vuoi contribuire?** Vedi [come contribuire al Lab](https://github.com/dataciviclab/dataciviclab/blob/main/docs/come-contribuire.md)

## Architettura

```
costituzione-italiana/
├── Costituzione.md                     ← testo vigente
├── data/                               ← 7 dataset in parquet + CSV
├── strumenti/                          ← 7 script di import/export
├── tests/                              ← 14 test
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
| Dataset Lab | clean_catalog | Varie |

## Licenza

- **Testo**: CC BY-SA 3.0 (da Wikisource)
- **Dati Corte Costituzionale**: CC BY-SA 3.0
- **Codice**: MIT
