-- MART: norme impugnate, una riga per (massima, norma)
--
-- Tabella esplosa per i consumer che lavorano sulla singola norma
-- (legal-graph `impugna`, analisi delle leggi più contestate).
-- Righe attese: ~87k.

SELECT
    m.id_massima,
    m.anno_pronuncia,
    m.numero_pronuncia,
    m.tipologia_pronuncia,
    m.esito,
    json_extract_string(n.value, '$.codice') AS norma_codice,
    json_extract_string(n.value, '$.descrizione') AS norma_descrizione,
    json_extract_string(n.value, '$.numero') AS norma_numero,
    json_extract_string(n.value, '$.data') AS norma_data,
    json_extract_string(n.value, '$.articolo') AS norma_articolo,
    json_extract_string(n.value, '$.specificazione_articolo') AS norma_specificazione_articolo,
    json_extract_string(n.value, '$.comma') AS norma_comma,
    json_extract_string(n.value, '$.specificazione_comma') AS norma_specificazione_comma
FROM clean_input m,
     json_each(m.norme) AS n
ORDER BY m.anno_pronuncia, m.numero_pronuncia, m.id_massima
