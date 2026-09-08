-- MART: parametri costituzionali per anno
--
-- Conta quante volte ogni articolo della Costituzione viene evocato come parametro,
-- con tasso di accoglimento per anno.
-- Primary key: anno_pronuncia, parametro_articolo

SELECT
    anno_pronuncia,
    parametro_articolo,
    COUNT(*) AS n_volte,
    SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
    SUM(CASE WHEN esito IN ('non_fondata', 'manifestamente_infondata') THEN 1 ELSE 0 END) AS n_respinte,
    SUM(CASE WHEN esito = 'inammissibile' THEN 1 ELSE 0 END) AS n_inammissibili,
    ROUND(
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(SUM(CASE WHEN esito IN ('illegittimo', 'non_fondata', 'manifestamente_infondata', 'inammissibile') THEN 1 ELSE 0 END), 0),
        1
    ) AS pct_accoglimento
FROM clean_input
WHERE parametro_articolo IS NOT NULL
  AND anno_pronuncia > 0
GROUP BY anno_pronuncia, parametro_articolo
ORDER BY anno_pronuncia, n_volte DESC
