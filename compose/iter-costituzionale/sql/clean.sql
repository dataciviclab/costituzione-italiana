-- CLEAN: iter_costituzionale — DDL costituzionali × revisioni promulgate
--
-- raw_input = revisioni_costituzionali clean (questo repo)
-- support   = senato_ddl / camera_ddl / camera_leggi (open-politica, GCS)
--
-- Una riga per proposta DDL (camera/senato), con campi revisioni matchati.
--
-- join_tier:
--   high   — chiave strutturata (URN camera o data+numero reale + overlap)
--   medium — titolo (famiglia istituzionale, non identità di legge)
-- ha_legge = 1 solo su tier=high.

WITH revisioni AS (
    SELECT
        urn AS rev_urn,
        codice_redazionale AS rev_codice,
        data AS rev_data,
        titolo AS rev_titolo,
        articoli_modificati AS rev_articoli,
        n_articoli AS rev_n_articoli,
        tipo AS rev_tipo,
        regexp_extract(urn, '(\d{4}-\d{2}-\d{2});(\d+)', 1)
            || ';' || regexp_extract(urn, '(\d{4}-\d{2}-\d{2});(\d+)', 2) AS legge_key_full,
        regexp_extract(urn, '(\d{4})-(\d{2}-\d{2});(\d+)', 1)
            || ';' || regexp_extract(urn, '(\d{4}-\d{2}-\d{2});(\d+)', 2) AS legge_key_year,
        regexp_extract(urn, '(\d{4}-\d{2}-\d{2});(\d+)', 2) AS rev_numero,
        lower(regexp_replace(COALESCE(titolo, ''), '[^a-z0-9 ]', '', 'g')) AS titolo_norm,
        list_filter(
            string_split(
                lower(regexp_replace(COALESCE(titolo, ''), '[^a-z0-9 ]', ' ', 'g')),
                ' '
            ),
            x -> length(trim(x)) >= 5
        ) AS titolo_tokens
    FROM raw_input
    WHERE tipo IN ('modifica_costituzione', 'altra_legge_costituzionale', 'statuto_speciale')
),

senato_raw AS (
    SELECT
        'senato' AS camera_o_senato,
        CAST(atto_num AS VARCHAR) AS atto_num,
        ddl_url AS atto_uri,
        titolo,
        data_presentazione,
        legislatura,
        stato,
        descr_iniziativa AS proponente,
        numero_legge,
        data_legge,
        urn_normattiva,
        natura,
        data_stato_ddl,
        NULL::BIGINT AS ddl_numero,
        NULL::VARCHAR AS urn_camera,
        CASE
            WHEN data_legge IS NOT NULL
             AND CAST(data_legge AS DATE) <> DATE '2100-01-01'
             AND numero_legge IS NOT NULL
                THEN CAST(CAST(data_legge AS DATE) AS VARCHAR) || ';' || CAST(numero_legge AS VARCHAR)
            ELSE NULL
        END AS legge_key_data,
        lower(regexp_replace(COALESCE(titolo, ''), '[^a-z0-9 ]', '', 'g')) AS titolo_norm,
        list_filter(
            string_split(
                lower(regexp_replace(COALESCE(titolo, ''), '[^a-z0-9 ]', ' ', 'g')),
                ' '
            ),
            x -> length(trim(x)) >= 5
        ) AS titolo_tokens
    FROM read_parquet({support.senato_ddl.outputs}, union_by_name = true)
    WHERE natura = 'costituzionale'
),

camera_raw AS (
    SELECT
        'camera' AS camera_o_senato,
        CAST(id_ddl AS VARCHAR) AS atto_num,
        atto_camera AS atto_uri,
        titolo,
        data_presentazione,
        legislatura,
        stato,
        primo_firmatario AS proponente,
        NULL::BIGINT AS numero_legge,
        NULL::DATE AS data_legge,
        NULL::VARCHAR AS urn_normattiva,
        'costituzionale' AS natura,
        NULL::TIMESTAMP AS data_stato_ddl,
        -- DDL number in titolo: "(2473-B)" → 2473
        TRY_CAST(regexp_extract(COALESCE(titolo, ''), '\((\d+)(?:-\w+)?\)', 1) AS BIGINT) AS ddl_numero,
        NULL::VARCHAR AS urn_camera,
        NULL::VARCHAR AS legge_key_data,
        lower(regexp_replace(COALESCE(titolo, ''), '[^a-z0-9 ]', '', 'g')) AS titolo_norm,
        list_filter(
            string_split(
                lower(regexp_replace(COALESCE(titolo, ''), '[^a-z0-9 ]', ' ', 'g')),
                ' '
            ),
            x -> length(trim(x)) >= 5
        ) AS titolo_tokens
    FROM read_parquet({support.camera_ddl.outputs}, union_by_name = true)
    WHERE upper(titolo) LIKE '%DI LEGGE COSTITUZIONALE%'
       OR upper(titolo) LIKE '%DISEGNO DI LEGGE COSTITUZIONALE%'
),

-- camera_leggi: chiave Normattiva quando presente (URN/GU)
-- Una riga per legge_camera: il clean OP partiziona per {year}
-- (una URI in un solo file year). Il QUALIFY resta solo difesa
-- se un consumatore unisse year non partizionati.
camera_leggi_raw AS (
    SELECT
        legge_camera,
        id_legge,
        titolo,
        tipo,
        data_promulgazione,
        legislatura,
        anno,
        urn_normattiva,
        gu_pubblicazione,
        ddl_numero,
        regexp_extract(COALESCE(urn_normattiva, ''), '(\d{4}-\d{2}-\d{2});(\d+)', 1)
            || ';' || regexp_extract(COALESCE(urn_normattiva, ''), '(\d{4}-\d{2}-\d{2});(\d+)', 2) AS legge_key_full,
        regexp_extract(COALESCE(urn_normattiva, ''), '(\d{4})(?:-\d{2}-\d{2})?;(\d+)', 1)
            || ';' || regexp_extract(COALESCE(urn_normattiva, ''), '(\d{4})(?:-\d{2}-\d{2})?;(\d+)', 2) AS legge_key_year,
        lower(regexp_replace(COALESCE(titolo, ''), '[^a-z0-9 ]', '', 'g')) AS titolo_norm
    FROM read_parquet({support.camera_leggi.outputs}, union_by_name = true)
    WHERE UPPER(COALESCE(tipo, '')) = 'COSTITUZIONALE'
       OR urn_normattiva LIKE '%legge.costituzionale%'
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY legge_camera
        ORDER BY
            CASE WHEN NULLIF(urn_normattiva, '') IS NOT NULL THEN 0 ELSE 1 END,
            data_promulgazione DESC NULLS LAST
    ) = 1
),

ddl_all AS (
    SELECT * FROM senato_raw
    UNION ALL
    SELECT * FROM camera_raw
),

ddl AS (
    SELECT *
    FROM (
        SELECT
            d.*,
            ROW_NUMBER() OVER (
                PARTITION BY camera_o_senato, atto_num
                ORDER BY
                    CASE
                        WHEN numero_legge IS NOT NULL
                         AND data_legge IS NOT NULL
                         AND CAST(data_legge AS DATE) <> DATE '2100-01-01'
                            THEN 0
                        ELSE 1
                    END,
                    CASE WHEN legge_key_data IS NOT NULL THEN 0 ELSE 1 END,
                    data_stato_ddl DESC NULLS LAST,
                    data_presentazione DESC NULLS LAST
            ) AS _rn
        FROM ddl_all d
    ) WHERE _rn = 1
),

-- ── HIGH 1: camera DDL → camera_leggi (ddl_numero+legislatura o titolo) → revisioni ──
-- ddl_numero Camera restarta per legislatura: senza qualifica si possono
-- collidere DDL di leg diverse (stessa classe del bug LC/PK OP #48/#50).
ddl_to_leggi AS (
    SELECT
        d.camera_o_senato,
        d.atto_num,
        d.legislatura AS ddl_legislatura,
        c.urn_normattiva AS urn_camera,
        c.legge_key_full AS legge_key_full_cam,
        c.legge_key_year AS legge_key_year_cam,
        c.ddl_numero AS ddl_numero_cam,
        c.legislatura AS legge_legislatura,
        c.gu_pubblicazione,
        c.titolo AS legge_titolo,
        CASE
            WHEN d.ddl_numero IS NOT NULL AND c.ddl_numero IS NOT NULL
             AND d.ddl_numero = c.ddl_numero
             AND d.legislatura IS NOT NULL AND c.legislatura IS NOT NULL
             AND d.legislatura = c.legislatura
                THEN 'ddl_numero'
            WHEN d.titolo_norm = c.titolo_norm THEN 'titolo_exatto'
            WHEN c.titolo_norm LIKE '%' || substring(d.titolo_norm FROM 1 FOR 60) || '%'
              OR d.titolo_norm LIKE '%' || substring(c.titolo_norm FROM 1 FOR 60) || '%'
                THEN 'titolo_containment'
            ELSE NULL
        END AS link_camera_leggi
    FROM ddl d
    JOIN camera_leggi_raw c
      ON (
            -- join strutturato solo con legislatura allineata
            d.ddl_numero IS NOT NULL AND c.ddl_numero IS NOT NULL
            AND d.ddl_numero = c.ddl_numero
            AND d.legislatura IS NOT NULL AND c.legislatura IS NOT NULL
            AND d.legislatura = c.legislatura
         OR d.titolo_norm = c.titolo_norm
         OR c.titolo_norm LIKE '%' || substring(d.titolo_norm FROM 1 FOR 60) || '%'
         OR d.titolo_norm LIKE '%' || substring(c.titolo_norm FROM 1 FOR 60) || '%'
      )
),

matched_urn_camera AS (
    SELECT
        d.camera_o_senato,
        d.atto_num,
        r.rev_urn,
        r.rev_data,
        r.rev_codice,
        r.rev_titolo,
        r.rev_articoli,
        r.rev_n_articoli,
        r.rev_tipo,
        l.urn_camera,
        l.gu_pubblicazione,
        'urn_camera' AS join_method,
        'high' AS join_quality,
        'high' AS join_tier
    FROM ddl_to_leggi l
    JOIN ddl d
      ON d.camera_o_senato = l.camera_o_senato
     AND d.atto_num = l.atto_num
    JOIN revisioni r
      ON r.rev_urn = l.urn_camera
      OR (l.legge_key_full_cam IS NOT NULL AND l.legge_key_full_cam = r.legge_key_full)
      OR (l.legge_key_year_cam IS NOT NULL AND l.legge_key_year_cam = r.legge_key_year)
),

-- ── HIGH 2: (data_legge reale, numero_legge) + overlap titoli ──
cand_data_num AS (
    SELECT
        d.camera_o_senato,
        d.atto_num,
        d.titolo_norm AS ddl_titolo_norm,
        d.titolo_tokens AS ddl_tokens,
        d.legge_key_data,
        r.rev_urn,
        r.rev_data,
        r.rev_codice,
        r.rev_titolo,
        r.rev_articoli,
        r.rev_n_articoli,
        r.rev_tipo,
        r.titolo_norm AS rev_titolo_norm,
        r.titolo_tokens AS rev_tokens,
        (
            SELECT COUNT(*)
            FROM unnest(d.titolo_tokens) AS t(tok)
            WHERE t.tok IN (SELECT unnest(r.titolo_tokens))
        ) AS n_common_tokens,
        least(length(d.titolo_tokens), length(r.titolo_tokens)) AS n_tokens_min
    FROM ddl d
    JOIN revisioni r
      ON d.legge_key_data IS NOT NULL
     AND d.legge_key_data = r.legge_key_full
),

matched_data_num AS (
    SELECT
        c.camera_o_senato,
        c.atto_num,
        c.rev_urn,
        c.rev_data,
        c.rev_codice,
        c.rev_titolo,
        c.rev_articoli,
        c.rev_n_articoli,
        c.rev_tipo,
        NULL::VARCHAR AS urn_camera,
        NULL::VARCHAR AS gu_pubblicazione,
        'data_numero' AS join_method,
        CASE
            WHEN (
                    c.ddl_titolo_norm LIKE '%' || substring(c.rev_titolo_norm FROM 1 FOR 45) || '%'
                 OR c.rev_titolo_norm LIKE '%' || substring(c.ddl_titolo_norm FROM 1 FOR 45) || '%'
                 OR (
                        c.n_common_tokens >= 4
                     AND c.n_tokens_min > 0
                     AND c.n_common_tokens * 1.0 / c.n_tokens_min >= 0.45
                 )
                )
                THEN 'high'
            WHEN (
                    c.n_common_tokens >= 1
                 OR c.ddl_titolo_norm LIKE '%' || substring(c.rev_titolo_norm FROM 1 FOR 50) || '%'
                 OR c.rev_titolo_norm LIKE '%' || substring(c.ddl_titolo_norm FROM 1 FOR 50) || '%'
                )
                THEN 'medium'
            ELSE NULL
        END AS join_quality,
        CASE
            WHEN (
                    c.ddl_titolo_norm LIKE '%' || substring(c.rev_titolo_norm FROM 1 FOR 45) || '%'
                 OR c.rev_titolo_norm LIKE '%' || substring(c.ddl_titolo_norm FROM 1 FOR 45) || '%'
                 OR (
                        c.n_common_tokens >= 4
                     AND c.n_tokens_min > 0
                     AND c.n_common_tokens * 1.0 / c.n_tokens_min >= 0.45
                 )
                )
                THEN 'high'
            WHEN (
                    c.n_common_tokens >= 1
                 OR c.ddl_titolo_norm LIKE '%' || substring(c.rev_titolo_norm FROM 1 FOR 50) || '%'
                 OR c.rev_titolo_norm LIKE '%' || substring(c.ddl_titolo_norm FROM 1 FOR 50) || '%'
                )
                THEN 'medium'
            ELSE NULL
        END AS join_tier
    FROM cand_data_num c
    WHERE (
            c.n_common_tokens >= 1
         OR c.ddl_titolo_norm LIKE '%' || substring(c.rev_titolo_norm FROM 1 FOR 50) || '%'
         OR c.rev_titolo_norm LIKE '%' || substring(c.ddl_titolo_norm FROM 1 FOR 50) || '%'
    )
      AND NOT EXISTS (
        SELECT 1 FROM matched_urn_camera m
        WHERE m.camera_o_senato = c.camera_o_senato
          AND m.atto_num = c.atto_num
    )
),

-- ── MEDIUM: titolo — solo se non già matchato su chiave strutturata ──
matched_titolo AS (
    SELECT
        d.camera_o_senato,
        d.atto_num,
        r.rev_urn,
        r.rev_data,
        r.rev_codice,
        r.rev_titolo,
        r.rev_articoli,
        r.rev_n_articoli,
        r.rev_tipo,
        NULL::VARCHAR AS urn_camera,
        NULL::VARCHAR AS gu_pubblicazione,
        'titolo' AS join_method,
        CASE
            WHEN d.titolo_norm = r.titolo_norm THEN 'high'
            ELSE 'medium'
        END AS join_quality,
        -- Titolo resta medium: identità di legge non documentata da chiave
        'medium' AS join_tier
    FROM ddl d
    JOIN revisioni r
      ON length(d.titolo_norm) > 30
     AND length(r.titolo_norm) > 30
     AND (
            d.titolo_norm = r.titolo_norm
         OR (
                (
                    r.titolo_norm LIKE '%' || substring(d.titolo_norm FROM 1 FOR 60) || '%'
                 OR d.titolo_norm LIKE '%' || substring(r.titolo_norm FROM 1 FOR 60) || '%'
                )
             AND (
                    (
                        SELECT COUNT(*)
                        FROM unnest(d.titolo_tokens) AS t(tok)
                        WHERE t.tok IN (SELECT unnest(r.titolo_tokens))
                    ) >= CASE
                        WHEN (d.titolo_norm LIKE '%modific%' OR d.titolo_norm LIKE '%revisione%')
                         AND (r.titolo_norm NOT LIKE '%modific%' AND r.titolo_norm NOT LIKE '%revisione%')
                            THEN 4
                        WHEN (r.titolo_norm LIKE '%modific%' OR r.titolo_norm LIKE '%revisione%')
                         AND (d.titolo_norm NOT LIKE '%modific%' AND d.titolo_norm NOT LIKE '%revisione%')
                            THEN 4
                        ELSE 3
                    END
                )
         )
    )
    WHERE NOT EXISTS (
        SELECT 1 FROM matched_urn_camera m
        WHERE m.camera_o_senato = d.camera_o_senato AND m.atto_num = d.atto_num
    )
      AND NOT EXISTS (
        SELECT 1 FROM matched_data_num m
        WHERE m.camera_o_senato = d.camera_o_senato AND m.atto_num = d.atto_num
          AND m.join_tier = 'high'
    )
),

matched AS (
    SELECT * FROM matched_urn_camera
    UNION ALL
    SELECT * FROM matched_data_num
    UNION ALL
    SELECT * FROM matched_titolo
),

final AS (
    SELECT
        d.camera_o_senato,
        d.atto_num,
        d.atto_uri,
        d.titolo,
        d.data_presentazione,
        d.legislatura,
        d.stato,
        d.proponente,
        d.numero_legge,
        d.data_legge,
        d.urn_normattiva,
        d.natura,
        d.ddl_numero,
        m.rev_urn,
        m.rev_data,
        m.rev_codice,
        m.rev_titolo,
        m.rev_articoli,
        m.rev_n_articoli,
        m.rev_tipo,
        m.urn_camera,
        m.gu_pubblicazione,
        COALESCE(m.join_method, 'nessuna') AS join_method,
        COALESCE(m.join_quality, 'none') AS join_quality,
        COALESCE(m.join_tier, 'none') AS join_tier,
        -- Solo tier high = identità di legge documentata
        CASE WHEN m.join_tier = 'high' AND m.rev_urn IS NOT NULL THEN 1 ELSE 0 END AS ha_legge,
        CASE
            WHEN d.camera_o_senato = 'senato'
             AND d.stato IS NOT NULL
             AND (
                    upper(d.stato) LIKE '%APPROVATO%'
                 OR upper(d.stato) LIKE '%APPR.%'
             ) THEN 1
            WHEN d.camera_o_senato = 'camera'
             AND d.stato IS NOT NULL
             AND upper(d.stato) LIKE '%APPROVATO%'
             AND upper(d.stato) LIKE '%DEFINITIVAMENTE%'
                THEN 1
            ELSE 0
        END AS stato_avanzato
    FROM ddl d
    LEFT JOIN matched m
      ON m.camera_o_senato = d.camera_o_senato
     AND m.atto_num = d.atto_num
)

SELECT
    camera_o_senato,
    atto_num,
    atto_uri,
    titolo,
    data_presentazione,
    legislatura,
    stato,
    proponente,
    numero_legge,
    data_legge,
    urn_normattiva,
    natura,
    ddl_numero,
    rev_urn,
    rev_data,
    rev_codice,
    rev_titolo,
    rev_articoli,
    rev_n_articoli,
    rev_tipo,
    urn_camera,
    gu_pubblicazione,
    join_method,
    join_quality,
    join_tier,
    ha_legge,
    stato_avanzato
FROM final
