-- MART: esiti per tipologia di giudizio
--
-- Distribuzione degli esiti raggruppata per tipo di giudizio.
-- Utile per capire se i conflitti di attribuzione hanno esiti diversi
-- dai giudizi di legittimità costituzionale.
-- Primary key: tipologia_giudizio

SELECT
    tipologia_giudizio,
    COUNT(*) AS n_massime,
    COUNT(DISTINCT anno_pronuncia || '-' || LPAD(CAST(numero_pronuncia AS VARCHAR), 4, '0')) AS n_sentenze,
    SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
    SUM(CASE WHEN esito IN ('non_fondata', 'manifestamente_infondata') THEN 1 ELSE 0 END) AS n_respinte,
    SUM(CASE WHEN esito = 'inammissibile' THEN 1 ELSE 0 END) AS n_inammissibili,
    ROUND(
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) * 100.0 /
        NULLIF(SUM(CASE WHEN esito IN ('illegittimo', 'non_fondata', 'manifestamente_infondata', 'inammissibile') THEN 1 ELSE 0 END), 0),
        1
    ) AS pct_accoglimento,
    MIN(anno_pronuncia) AS primo_anno,
    MAX(anno_pronuncia) AS ultimo_anno
FROM clean_input
WHERE tipologia_giudizio IS NOT NULL
  AND tipologia_giudizio != ''
GROUP BY tipologia_giudizio
ORDER BY n_massime DESC
