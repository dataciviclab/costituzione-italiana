-- MART: revisioni per articolo
--
-- Quante volte ogni articolo della Costituzione è stato modificato da una legge di revisione.
-- Solo le leggi con tipo = 'modifica_costituzione'.

SELECT
    val AS articolo,
    COUNT(*) AS n_modifiche
FROM clean_input, UNNEST(articoli_modificati) AS t(val)
WHERE val IS NOT NULL
  AND tipo = 'modifica_costituzione'
GROUP BY val
ORDER BY n_modifiche DESC
