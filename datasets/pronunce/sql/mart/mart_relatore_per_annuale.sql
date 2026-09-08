-- MART: relatore per anno
--
-- Quante pronunce ogni relatore ha emesso per anno.

SELECT
    anno_pronuncia,
    relatore_pronuncia,
    COUNT(*) AS n_pronunce,
    SUM(CASE WHEN tipologia_pronuncia = 'S' THEN 1 ELSE 0 END) AS n_sentenze,
    SUM(CASE WHEN tipologia_pronuncia = 'O' THEN 1 ELSE 0 END) AS n_ordinanze,
    SUM(CASE WHEN relatore_pronuncia != '' THEN 1 ELSE 0 END) AS n_con_relatore
FROM clean_input
WHERE anno_pronuncia > 0
GROUP BY anno_pronuncia, relatore_pronuncia
HAVING n_pronunce >= 5
ORDER BY anno_pronuncia, n_pronunce DESC
