-- CLEAN: citazioni della Costituzione nella legislazione ordinaria
--
-- Da italia-corpus: quali articoli vengono citati nelle leggi.

SELECT
    normalize_string(fonte_filename) AS fonte_filename,
    normalize_string(fonte_collezione) AS fonte_collezione,
    CAST(fonte_anno AS INTEGER) AS fonte_anno,
    normalize_string(fonte_tipo) AS fonte_tipo,
    CAST(articolo AS INTEGER) AS articolo,
    normalize_string(contesto) AS contesto
FROM raw_input
