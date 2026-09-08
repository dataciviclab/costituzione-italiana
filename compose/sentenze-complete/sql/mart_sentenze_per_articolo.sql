-- MART: sentenze per articolo — tasso di accoglimento per articolo

SELECT
    parametro_articolo,
    COUNT(*) AS n_casi,
    SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
    ROUND(
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0), 1
    ) AS pct_accoglimento,
    COUNT(DISTINCT relatore_pronuncia) AS n_relatori,
    MIN(anno_pronuncia) AS primo_anno,
    MAX(anno_pronuncia) AS ultimo_anno
FROM clean_input
WHERE parametro_articolo IS NOT NULL
GROUP BY parametro_articolo
HAVING n_casi >= 5
ORDER BY n_accolte DESC
