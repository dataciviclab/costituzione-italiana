-- CLEAN: anagrafica giudici costituzionali
--
-- Una riga per giudice con nome, eletto_da, date, nota biografica.

SELECT
    normalize_string(nome_cognome) AS nome_cognome,
    normalize_string(cognome) AS cognome,
    normalize_string(nome) AS nome,
    normalize_string(titolo) AS titolo,
    normalize_string(eletto_da) AS eletto_da,
    TRY_CAST(data_nomina AS DATE) AS data_nomina,
    TRY_CAST(data_giuramento AS DATE) AS data_giuramento,
    TRY_CAST(data_cessazione AS DATE) AS data_cessazione,
    normalize_string(nota_biografica) AS nota_biografica
FROM raw_input
