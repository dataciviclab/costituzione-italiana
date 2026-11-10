-- CLEAN: massime della Corte Costituzionale
--
-- Una riga per massima. `parametri` e `norme` sono due liste indipendenti
-- della stessa massima: restano JSON qui e vengono esplose nei mart
-- (`mart_massime_parametri`, `mart_massime_norme`). Mai prodotto cartesiano.

SELECT
    CAST(id_massima AS INTEGER) AS id_massima,
    CAST(anno_pronuncia AS INTEGER) AS anno_pronuncia,
    CAST(numero_pronuncia AS INTEGER) AS numero_pronuncia,
    normalize_string(tipologia_pronuncia) AS tipologia_pronuncia,
    normalize_string(tipologia_giudizio) AS tipologia_giudizio,
    TRY_CAST(strptime(NULLIF(data_decisione, ''), '%d/%m/%Y') AS DATE) AS data_decisione,
    TRY_CAST(strptime(NULLIF(data_deposito, ''), '%d/%m/%Y') AS DATE) AS data_deposito,
    -- esito derivato dal testo (la fonte non lo espone): per pronuncia, come prima
    normalize_string(esito) AS esito,
    normalize_string(titolo) AS titolo,
    normalize_string(testo) AS testo,
    normalize_string(parametri) AS parametri,
    normalize_string(norme) AS norme,
    CAST(n_parametri AS INTEGER) AS n_parametri,
    CAST(n_norme AS INTEGER) AS n_norme
FROM raw_input
