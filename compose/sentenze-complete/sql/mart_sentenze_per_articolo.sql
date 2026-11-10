-- MART: sentenze per articolo — tasso di accoglimento per articolo
--
-- Una riga per (massima, parametro costituzionale): `n_casi` è il numero
-- di volte che l'articolo è stato evocato, non il numero di righe del
-- vecchio prodotto cartesiano parametri×norme.

WITH parametri AS (
    SELECT
        c.anno_pronuncia,
        c.numero_pronuncia,
        c.relatore_pronuncia,
        c.esito,
        TRY_CAST(json_extract_string(p.value, '$.articolo') AS INTEGER) AS parametro_articolo,
        json_extract_string(p.value, '$.descrizione') AS parametro_descrizione
    FROM clean_input c,
         json_each(c.parametri) AS p
)

SELECT
    parametro_articolo,
    COUNT(*) AS n_casi,
    SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) AS n_accolte,
    ROUND(
        SUM(CASE WHEN esito = 'illegittimo' THEN 1 ELSE 0 END) * 100.0
        / NULLIF(COUNT(*), 0), 1
    ) AS pct_accoglimento,
    COUNT(DISTINCT relatore_pronuncia) AS n_relatori,
    MIN(anno_pronuncia) AS primo_anno,
    MAX(anno_pronuncia) AS ultimo_anno
FROM parametri
WHERE parametro_articolo IS NOT NULL
  AND parametro_descrizione = 'Costituzione'
GROUP BY parametro_articolo
HAVING n_casi >= 5
ORDER BY n_accolte DESC
