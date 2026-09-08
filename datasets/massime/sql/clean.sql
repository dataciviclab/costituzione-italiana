-- CLEAN: massime della Corte Costituzionale
--
-- Lettura diretta dal parquet prodotto da importa-massime.py.
-- Cast tipi + normalizzazione esiti + parsing date.

SELECT
    CAST(id_massima AS INTEGER) AS id_massima,
    CAST(anno_pronuncia AS INTEGER) AS anno_pronuncia,
    CAST(numero_pronuncia AS INTEGER) AS numero_pronuncia,
    normalize_string(tipologia_pronuncia) AS tipologia_pronuncia,
    normalize_string(tipologia_giudizio) AS tipologia_giudizio,
    TRY_CAST(data_decisione AS DATE) AS data_decisione,
    TRY_CAST(data_deposito AS DATE) AS data_deposito,
    normalize_string(esito) AS esito,
    normalize_string(titolo) AS titolo,
    normalize_string(testo) AS testo,
    normalize_string(parametro_codice) AS parametro_codice,
    normalize_string(parametro_descrizione) AS parametro_descrizione,
    CAST(NULLIF(parametro_articolo, '') AS INTEGER) AS parametro_articolo,
    normalize_string(parametro_comma) AS parametro_comma,
    normalize_string(norma_codice) AS norma_codice,
    normalize_string(norma_descrizione) AS norma_descrizione,
    normalize_string(norma_numero) AS norma_numero,
    TRY_CAST(norma_data AS DATE) AS norma_data,
    normalize_string(norma_articolo) AS norma_articolo,
    normalize_string(norma_specificazione_articolo) AS norma_specificazione_articolo,
    normalize_string(norma_comma) AS norma_comma,
    normalize_string(norma_specificazione_comma) AS norma_specificazione_comma
FROM raw_input
