-- CLEAN: citazioni della Costituzione nella legislazione ordinaria
--
-- Da italia-corpus `riferimenti` clean: archi con origine='costituzione'
-- (fold 2026-11). Il target non è un atto ma un articolo:
-- `bersaglio_id = 'costituzione:art:N'`.
--
-- `fonte_collezione` è derivata dal prefisso del path (prima colonna del
-- filename relativo): la clean di `riferimenti` non la espone.

SELECT
    normalize_string(fonte_filename) AS fonte_filename,
    normalize_string(split_part(fonte_filename, '/', 1)) AS fonte_collezione,
    CAST(fonte_anno AS INTEGER) AS fonte_anno,
    normalize_string(fonte_tipo) AS fonte_tipo,
    CAST(regexp_extract(bersaglio_id, 'art:([0-9]+)$', 1) AS INTEGER) AS articolo,
    normalize_string(contesto) AS contesto,
    -- occorrenze della stessa citazione nell'atto (il fold deduplica su
    -- atto+articolo): sommare `peso` conserva la semantica storica
    -- "una citazione per occorrenza" del consumer.
    CAST(peso AS BIGINT) AS peso
FROM raw_input
WHERE origine = 'costituzione'
  AND bersaglio_id IS NOT NULL
