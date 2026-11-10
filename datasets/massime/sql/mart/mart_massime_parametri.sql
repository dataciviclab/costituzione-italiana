-- MART: parametri costituzionali evocati, una riga per (massima, parametro)
--
-- Tabella esplosa per i consumer che lavorano sul singolo parametro
-- (dashboard, analisi, legal-graph). Il clean resta a grana massima con
-- la lista JSON: qui si unnest senza perdere l'id della massima.
-- Righe attese: ~112k (i parametri dichiarati dalle massime).

SELECT
    m.id_massima,
    m.anno_pronuncia,
    m.numero_pronuncia,
    m.tipologia_pronuncia,
    m.esito,
    json_extract_string(p.value, '$.codice') AS parametro_codice,
    json_extract_string(p.value, '$.descrizione') AS parametro_descrizione,
    json_extract_string(p.value, '$.numero') AS parametro_numero,
    json_extract_string(p.value, '$.data') AS parametro_data,
    TRY_CAST(json_extract_string(p.value, '$.articolo') AS INTEGER) AS parametro_articolo,
    json_extract_string(p.value, '$.specificazione_articolo') AS parametro_specificazione_articolo,
    json_extract_string(p.value, '$.comma') AS parametro_comma,
    json_extract_string(p.value, '$.specificazione_comma') AS parametro_specificazione_comma
FROM clean_input m,
     json_each(m.parametri) AS p
ORDER BY m.anno_pronuncia, m.numero_pronuncia, m.id_massima
