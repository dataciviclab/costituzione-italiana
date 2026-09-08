-- MART: giudici per origine
--
-- Quanti giudici sono stati eletti da ogni ente.

SELECT
    eletto_da,
    COUNT(*) AS n_giudici,
    MIN(data_nomina) AS prima_nomina,
    MAX(data_nomina) AS ultima_nomina,
    SUM(CASE WHEN data_cessazione IS NOT NULL THEN 1 ELSE 0 END) AS n_con_cessazione
FROM clean_input
WHERE eletto_da IS NOT NULL AND eletto_da != ''
GROUP BY eletto_da
ORDER BY n_giudici DESC
