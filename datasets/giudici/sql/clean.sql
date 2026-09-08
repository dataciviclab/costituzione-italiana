-- CLEAN: anagrafica giudici costituzionali
--
-- Una riga per giudice con nome, eletto_da, date, nota biografica.

SELECT
    normalize_string(nome_cognome) AS nome_cognome,
    normalize_string(cognome) AS cognome,
    normalize_string(nome) AS nome,
    normalize_string(titolo) AS titolo,
    normalize_string(eletto_da) AS eletto_da,
    TRY_CAST(strptime(NULLIF(data_nomina, ''), '%d/%m/%Y') AS DATE) AS data_nomina,
    TRY_CAST(strptime(NULLIF(data_giuramento, ''), '%d/%m/%Y') AS DATE) AS data_giuramento,
    TRY_CAST(strptime(NULLIF(data_cessazione, ''), '%d/%m/%Y') AS DATE) AS data_cessazione,
    normalize_string(nota_biografica) AS nota_biografica
FROM raw_input
