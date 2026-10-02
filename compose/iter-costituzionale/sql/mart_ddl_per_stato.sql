-- MART: DDL costituzionali per stato — dove si fermano le revisioni?

SELECT
    camera_o_senato,
    legislatura,
    stato,
    COUNT(*) AS n_proposte,
    SUM(ha_legge) AS n_con_legge_high,
    SUM(CASE WHEN join_tier = 'medium' THEN 1 ELSE 0 END) AS n_tier_medium,
    SUM(stato_avanzato) AS n_stato_avanzato,
    ROUND(100.0 * SUM(ha_legge) / NULLIF(COUNT(*), 0), 1) AS pct_con_legge_high
FROM clean_input
GROUP BY 1, 2, 3
ORDER BY camera_o_senato, legislatura, n_proposte DESC
