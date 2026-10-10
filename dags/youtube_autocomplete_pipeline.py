import os
from datetime import datetime, timedelta, timezone
from uuid import UUID

from airflow.sdk import dag, get_current_context, task

from youtube_opportunity.autocomplete import (
    fetch_autocomplete_response,
    parse_autocomplete_response,
)
from youtube_opportunity.storage import (
    get_raw_autocomplete_response,
    insert_raw_autocomplete_request,
    upsert_autocomplete_suggestions,
)


def get_database_url() -> str:
    database_url = os.environ.get("YOUTUBE_DATABASE_URL")

    if not database_url:
        raise RuntimeError("YOUTUBE_DATABASE_URL is not configured.")

    return database_url


@dag(
    dag_id="youtube_autocomplete_pipeline",
    start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
    schedule=None,
    catchup=False,
    tags=["youtube", "autocomplete", "raw", "staging"],
)
def youtube_autocomplete_pipeline():

    @task(
        retries=2,
        retry_delay=timedelta(seconds=30),
    )
    def extract_and_load_raw() -> str:
        database_url = get_database_url()
        context = get_current_context()

        response = fetch_autocomplete_response(
            query="python veri analizi",
            language="tr",
            country="TR",
        )

        request_id = insert_raw_autocomplete_request(
            database_url=database_url,
            requested_at=response.requested_at,
            requested_query="python veri analizi",
            requested_language="tr",
            requested_country="TR",
            endpoint_url=response.endpoint_url,
            request_parameters=response.request_parameters,
            http_status_code=response.status_code,
            response_content_type=response.content_type,
            response_charset=response.charset,
            response_headers=response.headers,
            response_body=response.body,
            airflow_dag_run_id=context["dag_run"].run_id,
        )

        print(f"Saved raw request: {request_id}")

        return str(request_id)

    @task
    def parse_and_load_staging(request_id_value: str) -> int:
        database_url = get_database_url()
        request_id = UUID(request_id_value)

        raw_body, charset = get_raw_autocomplete_response(
            database_url=database_url,
            request_id=request_id,
        )

        parsed_response = parse_autocomplete_response(
            raw_body=raw_body,
            charset=charset,
        )

        suggestion_count = upsert_autocomplete_suggestions(
            database_url=database_url,
            request_id=request_id,
            suggestions=parsed_response["suggestions"],
        )

        print(
            f"Saved {suggestion_count} staging suggestions "
            f"for request {request_id}"
        )

        return suggestion_count

    request_id = extract_and_load_raw()
    parse_and_load_staging(request_id)


youtube_autocomplete_pipeline()