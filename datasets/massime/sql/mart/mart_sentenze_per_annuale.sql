-- MART: sentenze per anno
--
-- Aggrega le massime per pronuncia e anno, con conteggi per esito.
-- Primary key: anno_pronuncia

SELECT
    anno_pronuncia,
    COUNT(DISTINCT anno_pronuncia || '-' || LPAD(CAST(numero_pronuncia AS VARCHAR), 4, '0')) AS n_sentenze,
    COUNT(*) AS n_massime,
    SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
    SUM(CASE WHEN esito IN ('non_fondata', 'manifestamente_infondata') THEN 1 ELSE 0 END) AS n_respinte,
    SUM(CASE WHEN esito = 'inammissibile' THEN 1 ELSE 0 END) AS n_inammissibili,
    SUM(CASE WHEN esito = 'misto' THEN 1 ELSE 0 END) AS n_misti,
    SUM(CASE WHEN esito = 'altro' THEN 1 ELSE 0 END) AS n_altro,
    ROUND(
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(SUM(CASE WHEN esito IN ('illegittimo', 'non_fondata', 'manifestamente_infondata', 'inammissibile') THEN 1 ELSE 0 END), 0),
        1
    ) AS pct_accoglimento
FROM clean_input
WHERE anno_pronuncia > 0
GROUP BY anno_pronuncia
ORDER BY anno_pronuncia
