-- MART: funnel conversione — proposte → legge (tier high), per camera e legislatura
--
-- n_con_legge     = DDL con ha_legge=1 (tier high)
-- n_leggi_distinte = rev_urn distinti tra quelle DDL (evita overcount sibling)

SELECT
    camera_o_senato,
    legislatura,
    COUNT(*) AS n_proposte,
    SUM(CASE WHEN join_tier != 'none' THEN 1 ELSE 0 END) AS n_con_revisione,
    SUM(ha_legge) AS n_con_legge,
    COUNT(DISTINCT CASE WHEN ha_legge = 1 THEN rev_urn END) AS n_leggi_distinte,
    ROUND(100.0 * SUM(ha_legge) / NULLIF(COUNT(*), 0), 1) AS pct_conversione,
    SUM(CASE WHEN join_tier = 'high' THEN 1 ELSE 0 END) AS n_tier_high,
    SUM(CASE WHEN join_tier = 'medium' THEN 1 ELSE 0 END) AS n_tier_medium,
    SUM(CASE WHEN join_method = 'urn_camera' THEN 1 ELSE 0 END) AS n_urn_camera,
    SUM(CASE WHEN join_method = 'data_numero' THEN 1 ELSE 0 END) AS n_data_numero,
    SUM(CASE WHEN join_method = 'titolo' THEN 1 ELSE 0 END) AS n_titolo,
    MIN(data_presentazione) AS prima_proposta,
    MAX(data_presentazione) AS ultima_proposta
FROM clean_input
GROUP BY 1, 2
ORDER BY camera_o_senato, legislatura
