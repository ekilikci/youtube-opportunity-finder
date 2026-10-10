import hashlib
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg.types.json import Jsonb


def insert_raw_autocomplete_request(
    database_url: str,
    *,
    requested_at: datetime,
    requested_query: str,
    requested_language: str,
    requested_country: str,
    endpoint_url: str,
    request_parameters: Mapping[str, str],
    http_status_code: int | None,
    response_content_type: str | None,
    response_charset: str | None,
    response_headers: Mapping[str, str],
    response_body: bytes | None,
    airflow_dag_run_id: str | None = None,
    error_message: str | None = None,
) -> UUID:
    request_id = uuid4()

    response_sha256 = (
        hashlib.sha256(response_body).hexdigest()
        if response_body is not None
        else None
    )

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO raw.youtube_autocomplete_request (
                    request_id,
                    requested_at,
                    requested_query,
                    requested_language,
                    requested_country,
                    endpoint_url,
                    request_parameters,
                    http_status_code,
                    response_content_type,
                    response_charset,
                    response_headers,
                    response_body,
                    response_sha256,
                    airflow_dag_run_id,
                    error_message
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s
                )
                """,
                (
                    request_id,
                    requested_at,
                    requested_query,
                    requested_language,
                    requested_country,
                    endpoint_url,
                    Jsonb(dict(request_parameters)),
                    http_status_code,
                    response_content_type,
                    response_charset,
                    Jsonb(dict(response_headers)),
                    response_body,
                    response_sha256,
                    airflow_dag_run_id,
                    error_message,
                ),
            )

    return request_id

def upsert_autocomplete_suggestions(
    database_url: str,
    *,
    request_id: UUID,
    suggestions: Sequence[Mapping[str, Any]],
) -> int:
    rows = [
        (request_id,
        suggestion["suggestion_position"],
        suggestion["echoed_query"],
        suggestion["suggestion_text"],
        suggestion["subtype_codes"],
        )
        for suggestion in suggestions
    ]

    if not rows:
        return 0

    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO staging.youtube_autocomplete_suggestion (
                    request_id,
                    suggestion_position,
                    echoed_query,
                    suggestion_text,
                    subtype_codes
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (
                    request_id,
                    suggestion_position
                )
                DO UPDATE SET
                    echoed_query = EXCLUDED.echoed_query,
                    suggestion_text = EXCLUDED.suggestion_text,
                    subtype_codes = EXCLUDED.subtype_codes,
                    parsed_at = CURRENT_TIMESTAMP
                """,
                rows,
            )

    return len(rows)

def get_raw_autocomplete_response(
    database_url: str,
    *,
    request_id: UUID,
) -> tuple[bytes, str]:
    with psycopg.connect(database_url) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    response_body,
                    response_charset
                FROM raw.youtube_autocomplete_request
                WHERE request_id = %s
                """,
                (request_id,),
            )

            row = cursor.fetchone()

    if row is None:
        raise LookupError(
            f"Raw autocomplete request not found: {request_id}"
        )

    response_body, response_charset = row

    if response_body is None or response_charset is None:
        raise ValueError(
            f"Raw response is incomplete: {request_id}"
        )

    return bytes(response_body), response_charset