-- MART: citazioni per articolo della Costituzione
--
-- Quante volte ogni articolo viene citato nella legislazione ordinaria.

SELECT
    articolo,
    COUNT(*) AS n_citazioni,
    COUNT(DISTINCT fonte_filename) AS n_fonti_diverse,
    MIN(fonte_anno) AS prima_citazione,
    MAX(fonte_anno) AS ultima_citazione,
    COUNT(DISTINCT fonte_tipo) AS n_tipi_fonte
FROM clean_input
WHERE articolo IS NOT NULL
GROUP BY articolo
ORDER BY n_citazioni DESC
