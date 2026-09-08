-- CLEAN: sentenze_complete — pronunce × massime × giudici
--
-- Una riga per (pronuncia, massima).  La pronuncia è la riga padre
-- (LEFT JOIN → una pronuncia senza massime resta con una riga).

WITH massime AS (
    SELECT * FROM read_parquet('{support.massime.clean}')
),
giudici AS (
    SELECT * FROM read_parquet('{support.giudici.clean}')
)

SELECT
    -- ── pronunce (raw_input) ────────────────────────────
    p.anno_pronuncia,
    p.numero_pronuncia,
    p.ecli,
    p.tipologia_pronuncia,
    p.presidente,
    p.relatore_pronuncia,
    p.redattore_pronuncia,
    p.data_decisione,
    p.data_deposito,
    p.collegio,
    p.dispositivo,

    -- ── massime ─────────────────────────────────────────
    m.esito,
    m.tipologia_giudizio,
    m.parametro_articolo,
    m.parametro_comma,
    m.norma_descrizione,
    m.norma_articolo,

    -- ── giudici (eletto_da del relatore) ────────────────
    g.eletto_da AS relatore_eletto_da,
    g.data_nomina AS relatore_nomina

FROM raw_input p
LEFT JOIN massime m
    ON  p.anno_pronuncia = m.anno_pronuncia
    AND p.numero_pronuncia = m.numero_pronuncia
LEFT JOIN giudici g
    ON  p.relatore_pronuncia = g.nome_cognome
