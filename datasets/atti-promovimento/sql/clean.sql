-- CLEAN: atti di promovimento pendenti (norme impugnate + parametri evocati)
--
-- Dalla Corte Costituzionale: quali norme vengono impugnate e con quale
-- parametro. La fonte è uno snapshot dei giudizi pendenti (4 registri:
-- ordinanze, ricorsi, conflitti tra enti/poteri), non una serie storica.
--
-- DISTINCT: la fonte ripete 7 parametri identici (stessa parte, articolo,
-- comma e norme). Una riga per (atto, parte, parametro, comma) è il grain
-- dichiarato nel primary_key.

SELECT DISTINCT
    normalize_string(tipo) AS tipo,
    CAST(anno AS INTEGER) AS anno,
    CAST(numero_atto AS INTEGER) AS numero_atto,
    CAST(numero_parte AS INTEGER) AS numero_parte,
    CAST(parametro_articolo AS INTEGER) AS parametro_articolo,
    normalize_string(parametro_comma) AS parametro_comma,
    normalize_string(norma_descrizione) AS norma_descrizione,
    normalize_string(norma_numero) AS norma_numero,
    normalize_string(norma_articolo) AS norma_articolo,
    normalize_string(norme_str) AS norme_str,
    CAST(n_norme AS INTEGER) AS n_norme
FROM raw_input
