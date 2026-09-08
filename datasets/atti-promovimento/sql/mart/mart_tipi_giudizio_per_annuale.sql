-- MART: tipi di giudizio per anno
--
-- Distribuzione degli atti di promovimento per tipo (ordinanza/ricorso) e anno.

SELECT
    anno,
    tipo,
    COUNT(*) AS n_atti,
    SUM(n_norme) AS n_norme_totali,
    COUNT(DISTINCT parametro_articolo) AS n_parametri_diversi
FROM clean_input
WHERE anno > 0
GROUP BY anno, tipo
ORDER BY anno, n_atti DESC
