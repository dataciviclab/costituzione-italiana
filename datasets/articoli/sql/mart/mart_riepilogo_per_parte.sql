-- MART: riepilogo per parte della Costituzione
--
-- Conta articoli, commi medi e disposizioni per parte.

SELECT
    parte,
    COUNT(*) AS n_articoli,
    SUM(COALESCE(commi, 0)) AS n_commi_totali,
    ROUND(AVG(COALESCE(commi, 0)), 1) AS commi_medi,
    SUM(CASE WHEN disposizione IS NOT NULL THEN 1 ELSE 0 END) AS n_disposizioni_transitorie,
    MIN(articolo) AS primo_articolo,
    MAX(articolo) AS ultimo_articolo
FROM clean_input
GROUP BY parte
ORDER BY MIN(COALESCE(articolo, 999))
