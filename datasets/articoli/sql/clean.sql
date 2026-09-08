-- CLEAN: articoli della Costituzione Italiana
--
-- Estratti da Costituzione.md via estrai-articoli.py.

SELECT
    CAST(articolo AS INTEGER) AS articolo,
    normalize_string(disposizione) AS disposizione,
    normalize_string(parte) AS parte,
    normalize_string(titolo) AS titolo,
    normalize_string(sezione) AS sezione,
    normalize_string(heading) AS heading,
    normalize_string(testo) AS testo,
    CAST(commi AS INTEGER) AS commi
FROM raw_input
