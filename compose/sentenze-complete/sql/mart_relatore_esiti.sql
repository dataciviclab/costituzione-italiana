-- MART: relatore × esiti — quali relatori hanno più sentenze illegittime?

SELECT
    relatore_pronuncia,
    COUNT(*) AS n_pronunce,
    SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_illegittime,
    ROUND(
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0), 1
    ) AS pct_illegittime,
    COUNT(DISTINCT parametro_articolo) AS n_articoli_diversi,
    MIN(anno_pronuncia) AS primo_anno,
    MAX(anno_pronuncia) AS ultimo_anno
FROM clean_input
WHERE relatore_pronuncia IS NOT NULL
  AND relatore_pronuncia != ''
GROUP BY relatore_pronuncia
HAVING n_pronunce >= 10
ORDER BY n_illegittime DESC
