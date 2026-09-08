-- MART: composizione collegio
--
-- Statistiche sulla composizione dei collegi giudicanti.

SELECT
    presidente,
    COUNT(*) AS n_pronunce,
    MIN(anno_pronuncia) AS primo_anno,
    MAX(anno_pronuncia) AS ultimo_anno,
    COUNT(DISTINCT anno_pronuncia) AS n_anni_attivi
FROM clean_input
WHERE presidente IS NOT NULL AND presidente != ''
GROUP BY presidente
ORDER BY n_pronunce DESC
