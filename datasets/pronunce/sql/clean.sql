-- CLEAN: pronunce della Corte Costituzionale (testo integrale)
--
-- Una riga per pronuncia con presidente, relatore, collegio, testo, dispositivo.

SELECT
    CAST(anno_pronuncia AS INTEGER) AS anno_pronuncia,
    CAST(numero_pronuncia AS INTEGER) AS numero_pronuncia,
    normalize_string(ecli) AS ecli,
    normalize_string(tipologia_pronuncia) AS tipologia_pronuncia,
    normalize_string(presidente) AS presidente,
    normalize_string(relatore_pronuncia) AS relatore_pronuncia,
    normalize_string(redattore_pronuncia) AS redattore_pronuncia,
    TRY_CAST(data_decisione AS DATE) AS data_decisione,
    TRY_CAST(data_deposito AS DATE) AS data_deposito,
    normalize_string(collegio) AS collegio,
    normalize_string(testo) AS testo,
    normalize_string(dispositivo) AS dispositivo
FROM raw_input
