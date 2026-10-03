-- MART: revisioni promulgate con storico parlamentare
--
-- Una riga per legge (rev_urn). n_ddl_distinte = proposte collegate;
-- n_ddl_ha_legge = quante di quelle hanno join_tier=high su questa stessa legge.

SELECT
    rev_urn,
    rev_data,
    rev_codice,
    rev_titolo,
    rev_tipo,
    rev_n_articoli,
    rev_articoli,
    COUNT(*) AS n_ddl_collegate,
    COUNT(DISTINCT camera_o_senato || ':' || atto_num) AS n_ddl_distinte,
    SUM(ha_legge) AS n_ddl_ha_legge,
    MIN(data_presentazione) AS prima_ddl,
    MAX(data_presentazione) AS ultima_ddl,
    STRING_AGG(DISTINCT join_method, ', ' ORDER BY join_method) AS join_methods,
    STRING_AGG(DISTINCT join_tier, ', ' ORDER BY join_tier) AS join_tiers,
    MAX(CASE WHEN ha_legge = 1 THEN 1 ELSE 0 END) AS confermata_da_legge,
    MAX(CASE WHEN urn_camera IS NOT NULL THEN urn_camera END) AS urn_camera,
    MAX(CASE WHEN gu_pubblicazione IS NOT NULL THEN gu_pubblicazione END) AS gu_pubblicazione
FROM clean_input
WHERE rev_urn IS NOT NULL
GROUP BY 1, 2, 3, 4, 5, 6, 7
ORDER BY rev_data DESC
