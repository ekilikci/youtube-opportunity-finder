BEGIN;

CREATE TABLE IF NOT EXISTS raw.youtube_autocomplete_request (
    request_id UUID PRIMARY KEY,

    requested_at TIMESTAMPTZ NOT NULL,
    requested_query TEXT NOT NULL,
    requested_language VARCHAR(10) NOT NULL,
    requested_country VARCHAR(10) NOT NULL,

    endpoint_url TEXT NOT NULL,
    request_parameters JSONB NOT NULL,

    http_status_code SMALLINT,
    response_content_type TEXT,
    response_charset TEXT,
    response_headers JSONB,
    response_body BYTEA,
    response_sha256 CHAR(64),

    airflow_dag_run_id TEXT,
    error_message TEXT,
    ingested_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_http_status_code
        CHECK (
            http_status_code IS NULL
            OR http_status_code BETWEEN 100 AND 599
        ),

    CONSTRAINT valid_response_sha256
        CHECK (
            response_sha256 IS NULL
            OR response_sha256 ~ '^[0-9a-f]{64}$'
        )
);

CREATE INDEX IF NOT EXISTS idx_autocomplete_request_requested_at
    ON raw.youtube_autocomplete_request (requested_at);

CREATE INDEX IF NOT EXISTS idx_autocomplete_request_query_locale
    ON raw.youtube_autocomplete_request (
        requested_query,
        requested_language,
        requested_country
    );

CREATE TABLE IF NOT EXISTS staging.youtube_autocomplete_suggestion (
    request_id UUID NOT NULL,
    suggestion_position SMALLINT NOT NULL,

    echoed_query TEXT NOT NULL,
    suggestion_text TEXT NOT NULL,
    subtype_codes INTEGER[] NOT NULL DEFAULT '{}',

    parsed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (
        request_id,
        suggestion_position
    ),

    CONSTRAINT fk_autocomplete_suggestion_request
        FOREIGN KEY (request_id)
        REFERENCES raw.youtube_autocomplete_request (request_id),

    CONSTRAINT valid_suggestion_position
        CHECK (suggestion_position >= 0),

    CONSTRAINT non_empty_suggestion_text
        CHECK (length(trim(suggestion_text)) > 0)
);

CREATE INDEX IF NOT EXISTS idx_autocomplete_suggestion_text
    ON staging.youtube_autocomplete_suggestion (suggestion_text);

COMMIT;