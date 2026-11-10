# Modello dati

Grain, chiavi e limiti dei dataset. Per l'accesso: README.

## Dataset

| Slug | Grain | Chiave | Copertura |
|---|---|---|---|
| `articoli_costituzione` | 1 riga per articolo/disposizione | `parte, disposizione, articolo` | 139 articoli + 18 transitorie |
| `pronunce_corte_costituzionale` | 1 riga per pronuncia | `anno_pronuncia, numero_pronuncia` | 1956-2026, 22.428 |
| `massime_corte_costituzionale` | 1 riga per massima | `id_massima` | 1956-2026, 46.665 |
| `giudici_corte_costituzionale` | 1 riga per voce anagrafica | `nome_cognome` | 136 voci |
| `citazioni_costituzionali` | 1 riga per atto × articolo | `fonte_filename, articolo` | 4.771 atti, 9.993 coppie |
| `revisioni_costituzionali` | 1 riga per legge | `urn` | 50 leggi, 1948-2026 |
| `atti_promovimento_corte_costituzionale` | 1 riga per atto × parte × parametro × comma | `tipo, anno, numero_atto, numero_parte, parametro_articolo, parametro_comma` | snapshot pendenti 2024-2026, 993 |
| `sentenze_complete` (compose) | 1 riga per pronuncia × massima | `anno_pronuncia, numero_pronuncia, id_massima` | 46.718 |
| `iter_costituzionale` (compose) | 1 riga per DDL × revisione | `camera_o_senato, atto_num, rev_urn` | 2.737 proposte, leg. XIII-XIX |

## Massime: due liste indipendenti

La fonte espone per ogni massima due liste **non accoppiate**:
`parametri` (articoli della Costituzione evocati) e `norme` (disposizioni
impugnate). Nel clean restano JSON:

```
massime_corte_costituzionale.clean
  id_massima, anno_pronuncia, numero_pronuncia, esito, titolo, testo,
  parametri (JSON), norme (JSON), n_parametri, n_norme
```

Le tabelle piatte sono nei mart, una riga per elemento:

- `mart_massime_parametri` — 112.187 righe (massima × parametro)
- `mart_massime_norme` — 86.962 righe (massima × norma)

Non fare il prodotto cartesiano delle due liste: era il bug storico
(267.546 righe da 46.665 massime, 6.276 massime perse).

## Pronunce

`collegio` ed `epigrafe` sono valorizzati per tutte le 22.428 pronunce;
`testo` (motivazione) per 12.196 (54,4%, tutto il disponibile upstream).
Il dispositivo è sempre presente.

## Atti pendenti

La fonte open data pubblica solo i **registri dei giudizi pendenti**
(ordinanze, ricorsi, conflitti tra enti, conflitti tra poteri), non la
serie storica degli atti di promovimento. Il dataset è uno snapshot
2024-2026: non usarlo per serie storiche. Per il parametro storico usare
le massime (`mart_massime_parametri`, 1956-2026).

## Limiti dichiarati

- **Citazioni**: solo le 19 collezioni di italia-corpus (4.771 atti), non
  tutte le leggi ordinarie. `peso` = occorrenze della stessa citazione.
- **Esito**: derivato dal testo della massima (regex), non un campo della
  fonte; circa un terzo resta `altro`.
- **Giudici**: 136 voci come nell'anagrafica ufficiale, incluse 11 voci
  collettive presenti a monte.
- **Iter**: legislature XIII-XIX, limite delle fonti open-politica.

## Contratto per i consumer

Per analisi sull'articolo evocato usare `mart_massime_parametri` o
`mart_parametri_per_annuale`; per le norme impugnate `mart_massime_norme`.
Il clean `massime` è la tabella canonica della massima (testo, esito,
liste JSON), non una tabella piatta parametro/norma.
