-- MART: parametri costituzionali per anno
--
-- Esplode la lista JSON `parametri` di ogni massima: una riga per
-- (massima, parametro). Filtra i soli parametri che sono articoli della
-- Costituzione (`descrizione='Costituzione'`): statuti speciali, CEDU,
-- TFUE e leggi sono parametri di rango diverso e non vanno mescolati.
-- Primary key: anno_pronuncia, parametro_articolo

WITH parametri AS (
    SELECT
        m.anno_pronuncia,
        m.esito,
        TRY_CAST(json_extract_string(p.value, '$.articolo') AS INTEGER) AS parametro_articolo,
        json_extract_string(p.value, '$.descrizione') AS parametro_descrizione
    FROM clean_input m,
         json_each(m.parametri) AS p
    WHERE m.anno_pronuncia > 0
)

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
FROM parametri
WHERE parametro_articolo IS NOT NULL
  AND parametro_descrizione = 'Costituzione'
GROUP BY anno_pronuncia, parametro_articolo
ORDER BY anno_pronuncia, n_volte DESC
