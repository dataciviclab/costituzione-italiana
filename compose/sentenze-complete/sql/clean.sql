-- CLEAN: sentenze_complete — pronunce × massime × giudici
--
-- Una riga per (pronuncia, massima).  La pronuncia è la riga padre
-- (LEFT JOIN → una pronuncia senza massime resta con una riga).
--
-- Match anagrafica (#30):
--   presidente  → normalizzato (solo lettere) su cognome/nome; prefisso
--                 solo se unico candidato; omopoliti senza iniziale → NULL
--   relatore   → prima uguaglianza esatta, fallback normalizzato
--   righe anagrafica multi-persona (cognome con " - ") escluse dal lato presidente

WITH massime AS (
    SELECT * FROM read_parquet('{support.massime.clean}')
),
giudici_all AS (
    SELECT
        g.nome_cognome,
        g.eletto_da,
        g.data_nomina,
        regexp_replace(lower(trim(g.nome_cognome)), '[^a-z]', '', 'g') AS nome_norm,
        regexp_replace(lower(trim(g.cognome)), '[^a-z]', '', 'g') AS cognome_norm
    FROM read_parquet('{support.giudici.clean}') g
    WHERE g.nome_cognome IS NOT NULL
),
giudici_single AS (
    -- Esclude voci collettive tipo "Marta Cartabia - Daria de Pretis - …"
    SELECT
        g.nome_cognome,
        g.eletto_da,
        g.data_nomina,
        regexp_replace(lower(trim(g.nome_cognome)), '[^a-z]', '', 'g') AS nome_norm,
        regexp_replace(lower(trim(g.cognome)), '[^a-z]', '', 'g') AS cognome_norm
    FROM read_parquet('{support.giudici.clean}') g
    WHERE g.nome_cognome IS NOT NULL
      AND (
          g.cognome IS NULL
          OR g.cognome NOT LIKE '% - %'
      )
),
pronunce AS (
    SELECT
        p.*,
        regexp_replace(lower(trim(p.presidente)), '[^a-z]', '', 'g') AS presidente_norm,
        regexp_replace(lower(trim(p.relatore_pronuncia)), '[^a-z]', '', 'g') AS relatore_norm
    FROM raw_input p
),
presidente_cand AS (
    SELECT
        p.anno_pronuncia,
        p.numero_pronuncia,
        g.nome_cognome AS presidente_giudice,
        g.eletto_da AS presidente_eletto_da,
        g.data_nomina AS presidente_nomina,
        CASE
            WHEN g.cognome_norm = p.presidente_norm THEN 0
            WHEN g.nome_norm = p.presidente_norm THEN 1
            ELSE 2
        END AS match_rank,
        COUNT(*) OVER (
            PARTITION BY p.anno_pronuncia, p.numero_pronuncia
        ) AS n_cand
    FROM pronunce p
    JOIN giudici_single g
        ON  g.cognome_norm = p.presidente_norm
        OR  g.nome_norm = p.presidente_norm
        OR  g.cognome_norm LIKE p.presidente_norm || '%'
    WHERE p.presidente IS NOT NULL
      AND trim(p.presidente) <> ''
),
presidente_match AS (
    SELECT
        anno_pronuncia,
        numero_pronuncia,
        presidente_giudice,
        presidente_eletto_da,
        presidente_nomina
    FROM presidente_cand
    WHERE n_cand = 1 OR match_rank = 0
    QUALIFY row_number() OVER (
        PARTITION BY anno_pronuncia, numero_pronuncia
        ORDER BY match_rank, presidente_giudice
    ) = 1
),
relatore_cand AS (
    SELECT
        p.anno_pronuncia,
        p.numero_pronuncia,
        g.nome_cognome AS relatore_giudice,
        g.eletto_da AS relatore_eletto_da,
        g.data_nomina AS relatore_nomina,
        CASE
            WHEN g.nome_cognome = p.relatore_pronuncia THEN 0
            ELSE 1
        END AS match_rank
    FROM pronunce p
    JOIN giudici_all g
        ON  g.nome_cognome = p.relatore_pronuncia
        OR  g.nome_norm = p.relatore_norm
    WHERE p.relatore_pronuncia IS NOT NULL
      AND trim(p.relatore_pronuncia) <> ''
),
relatore_match AS (
    SELECT
        anno_pronuncia,
        numero_pronuncia,
        relatore_giudice,
        relatore_eletto_da,
        relatore_nomina
    FROM relatore_cand
    QUALIFY row_number() OVER (
        PARTITION BY anno_pronuncia, numero_pronuncia
        ORDER BY match_rank, relatore_giudice
    ) = 1
)

SELECT
    -- ── pronunce ─────────────────────────────────────────
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

    -- ── anagrafica: relatore (esatto → normalizzato) ────
    pr_relatore.relatore_eletto_da,
    pr_relatore.relatore_nomina,
    pr_relatore.relatore_giudice,

    -- ── anagrafica: presidente (normalizzato) ───────────
    pr_pres.presidente_giudice,
    pr_pres.presidente_eletto_da,
    pr_pres.presidente_nomina

FROM pronunce p
LEFT JOIN massime m
    ON  p.anno_pronuncia = m.anno_pronuncia
    AND p.numero_pronuncia = m.numero_pronuncia
LEFT JOIN relatore_match pr_relatore
    ON  p.anno_pronuncia = pr_relatore.anno_pronuncia
    AND p.numero_pronuncia = pr_relatore.numero_pronuncia
LEFT JOIN presidente_match pr_pres
    ON  p.anno_pronuncia = pr_pres.anno_pronuncia
    AND p.numero_pronuncia = pr_pres.numero_pronuncia
