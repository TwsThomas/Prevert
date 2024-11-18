WITH events AS(
    SELECT
        timestamp,
        text_tok,
        source, -- ["localhost", "web"]
        action, -- ["create", "update", "delete"]
        -- if action = "update"
        field,
        new_value,
        -- if action = "create"
        create_title,
        create_author,
        create_note,
    FROM `prevert.v1.events`
),

update_create AS(
    SELECT
        timestamp,
        timestamp as updated_timestamp,
        STRUCT(
            create_title as title,
            create_author as author,
            text_tok as text,
            CAST(Null as string) as book,
            source,
            CAST(Null as float64) as confiance,
            CAST(Null as float64) as nb_like,
            CAST(Null as float64) as page,
            CAST(Null as string) as url
        ) AS quote, -- everything we'd scrapped
        
        STRUCT(
            "𝄞" as quote_react,
            cast(Null as string) as note
        ) AS extra, -- extra info added by user
        
        STRUCT(
            text_tok as text_tok,
            CAST(Null as int) as nb_char,
            CAST(Null as int) as nb_lines,
            cast(null as boolean) as haiku,
            cast(null as boolean) as sonnet
        ) AS info, -- info post computed on local

    FROM events
    WHERE action = "create"
),

update_title AS(
    SELECT
        text_tok,
        MAX(timestamp) as updated_timestamp,
        ARRAY_AGG(STRUCT(new_value, timestamp) ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)].new_value as new_title
    FROM events
    WHERE action = "update" and field = "title"
    GROUP BY text_tok
),

update_author AS(
    SELECT
        text_tok,
        MAX(timestamp) as updated_timestamp,
        ARRAY_AGG(STRUCT(new_value, timestamp) ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)].new_value as new_author
    FROM events
    WHERE action = "update" and field = "author"
    GROUP BY text_tok
),

update_text AS(
    SELECT
        text_tok,
        MAX(timestamp) as updated_timestamp,
        ARRAY_AGG(STRUCT(new_value, timestamp) ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)].new_value as new_text
    FROM events
    WHERE action = "update" and field = "text"
    GROUP BY text_tok
),

update_vo AS(
    SELECT
        text_tok,
        MAX(timestamp) as updated_timestamp,
        ARRAY_AGG(STRUCT(new_value, timestamp) ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)].new_value as new_vo
    FROM events
    WHERE action = "update" and field = "vo"
    GROUP BY text_tok
),

update_react AS(
    SELECT
        text_tok,
        MAX(timestamp) as updated_timestamp,
        STRING_AGG(new_value) as new_quote_react
    FROM events
    WHERE action = "update" and field = "react"
    GROUP BY text_tok
),

update_note AS(
    SELECT
        text_tok,
        MAX(timestamp) as updated_timestamp,
        ARRAY_AGG(STRUCT(new_value, timestamp) ORDER BY timestamp DESC LIMIT 1)[OFFSET(0)].new_value as new_note
    FROM events
    WHERE action = "update" and field = "note"
    GROUP BY text_tok
),

update_delete AS(
    SELECT
        text_tok,
        MAX(timestamp) as updated_timestamp,
        TRUE as is_delete
    FROM events
    WHERE action = "delete"
    GROUP BY text_tok
),

raw_data AS(
    SELECT
        TIMESTAMP("2024-11-17 00:00:00") as timestamp,
        IF(title = "nan", Null, title) as title,
        IF(vo = "nan", Null, vo) as vo,
        * except(title,vo),
    from `prevert.v1.raw_data_parquet_17_nov` -- raw data from the 17th of November 2024
),

final AS(    
SELECT
    r.timestamp,
    GREATEST(
    COALESCE(r.timestamp, "2024-11-17 00:00:00"),
    COALESCE(update_title.updated_timestamp, "2024-11-17 00:00:00"),
    COALESCE(update_author.updated_timestamp, "2024-11-17 00:00:00"),
    COALESCE(update_text.updated_timestamp, "2024-11-17 00:00:00"),
    COALESCE(update_vo.updated_timestamp, "2024-11-17 00:00:00"),
    COALESCE(update_react.updated_timestamp, "2024-11-17 00:00:00"),
    COALESCE(update_note.updated_timestamp, "2024-11-17 00:00:00"),
    COALESCE(update_delete.updated_timestamp, "2024-11-17 00:00:00")) as updated_timestamp,

    STRUCT(
        COALESCE(update_title.new_title, r.title) as title,
        COALESCE(update_author.new_author, r.author) as author,
        COALESCE(update_text.new_text, r.text) as text,
        r.book,
        r.source,
        r.confiance,
        r.nb_like,
        r.page,
        r.url
    ) AS quote, -- everything we'd scrapped
    
    STRUCT(
        COALESCE(update_react.new_quote_react, r.quote_react) as quote_react,
        COALESCE(update_note.new_note, r.vo) as note
    ) AS extra, -- extra info added by user
    
    STRUCT(
        r.text_tok,
        r.nb_char,
        r.nb_lines,
        r.haiku,
        r.sonnet
    ) AS info, -- info post computed on local

from raw_data r
left join update_title on r.text_tok = update_title.text_tok
left join update_vo on r.text_tok = update_vo.text_tok
left join update_react on r.text_tok = update_react.text_tok
left join update_delete on r.text_tok = update_delete.text_tok
left join update_note on r.text_tok = update_note.text_tok
left join update_author on r.text_tok = update_author.text_tok
left join update_text on r.text_tok = update_text.text_tok
where update_delete.is_delete is null -- remove the deleted events
)

select * from final
where updated_timestamp > "2024-11-17 10:00:00"
union all 
select * from update_create