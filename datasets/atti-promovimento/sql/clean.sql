-- CLEAN: atti di promovimento (norme impugnate + parametri evocati)
--
-- Dalla Corte Costituzionale: quali norme vengono impugnate e con quale parametro.

SELECT
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
