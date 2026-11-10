-- MART: relatore × esiti — quali relatori hanno più sentenze illegittime?
--
-- L'unità è la pronuncia (non la massima): esito e relatore sono della
-- decisione. `n_articoli_diversi` esplode i parametri JSON delle massime
-- e conta i soli articoli della Costituzione.

WITH relatori AS (
    SELECT
        relatore_pronuncia,
        COUNT(DISTINCT (anno_pronuncia, numero_pronuncia)) AS n_pronunce,
        COUNT(DISTINCT CASE
            WHEN esito = 'illegittimo' THEN (anno_pronuncia, numero_pronuncia)
        END) AS n_illegittime,
        MIN(anno_pronuncia) AS primo_anno,
        MAX(anno_pronuncia) AS ultimo_anno
    FROM clean_input
    WHERE relatore_pronuncia IS NOT NULL
      AND relatore_pronuncia != ''
    GROUP BY relatore_pronuncia
),
articoli AS (
    SELECT
        c.relatore_pronuncia,
        COUNT(DISTINCT TRY_CAST(json_extract_string(p.value, '$.articolo') AS INTEGER)) AS n_articoli_diversi
    FROM clean_input c,
         json_each(c.parametri) AS p
    WHERE c.relatore_pronuncia IS NOT NULL
      AND c.relatore_pronuncia != ''
      AND json_extract_string(p.value, '$.descrizione') = 'Costituzione'
    GROUP BY c.relatore_pronuncia
)

SELECT
    r.relatore_pronuncia,
    r.n_pronunce,
    r.n_illegittime,
    ROUND(r.n_illegittime * 100.0 / NULLIF(r.n_pronunce, 0), 1) AS pct_illegittime,
    COALESCE(a.n_articoli_diversi, 0) AS n_articoli_diversi,
    r.primo_anno,
    r.ultimo_anno
FROM relatori r
LEFT JOIN articoli a USING (relatore_pronuncia)
WHERE r.n_pronunce >= 10
ORDER BY r.n_illegittime DESC
