-- CLEAN: leggi di revisione costituzionale
--
-- Da italia-corpus: quali articoli della Costituzione sono stati modificati.

SELECT
    normalize_string(urn) AS urn,
    normalize_string(codice_redazionale) AS codice_redazionale,
    TRY_CAST(data AS DATE) AS data,
    normalize_string(titolo) AS titolo,
    articoli_modificati,
    CAST(n_articoli AS INTEGER) AS n_articoli,
    normalize_string(tipo) AS tipo
FROM raw_input
