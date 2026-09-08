-- MART: parametri costituzionali per anno (atti di promovimento)
--
-- Conta quanti atti di promovimento evocano ogni articolo della Costituzione.
-- Differisce dalle massime: qui contiamo gli atti pendenti, non le sentenze.

SELECT
    anno,
    parametro_articolo,
    COUNT(*) AS n_atti,
    COUNT(DISTINCT numero_atto) AS n_atti_unici,
    SUM(n_norme) AS n_norme_totali
FROM clean_input
WHERE parametro_articolo IS NOT NULL
  AND anno > 0
GROUP BY anno, parametro_articolo
ORDER BY anno, n_atti DESC
