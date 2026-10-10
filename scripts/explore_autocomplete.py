import argparse
import hashlib
from html import parser
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from youtube_opportunity.autocomplete import (
    parse_autocomplete_response,
)
from youtube_opportunity.storage import (
    insert_raw_autocomplete_request,
    upsert_autocomplete_suggestions,
)

BASE_URL = "https://suggestqueries.google.com/complete/search"

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explore YouTube autocomplete responses."
    )
    parser.add_argument("--query", required=True)
    parser.add_argument("--language", default="tr")
    parser.add_argument("--country", default="TR")
    parser.add_argument(
        "--save-to-database",
        action="store_true",
        help="Save the raw response to PostgreSQL.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/discovery"),
    )
    return parser.parse_args()


def safe_filename(value: str) -> str:
    """Return a safe filename for the given value."""
    normalized = re.sub(r"[^\w-]+", "_", value.strip())
    return normalized.strip("_") or "empty-query"

def main() -> None:
    args = parse_arguments()
    parameters = {
        "client": "firefox",
        "ds": "yt",
        "hl": args.language,
        "gl": args.country,
        "q": args.query,
    }

    request_url = f"{BASE_URL}?{urlencode(parameters)}"
    request = Request(
        request_url,
        headers={
            "User-Agent": "youtube-opportunity-finder/0.1",
        },
    )

    requested_at = datetime.now(timezone.utc)

    with urlopen(request, timeout=30) as response:
        raw_body = response.read()
        response_sha256 = hashlib.sha256(raw_body).hexdigest()
        status_code = response.status
        response_headers = dict(response.headers.items())
        content_type = response.headers.get_content_type()
        charset = response.headers.get_content_charset() or "utf-8"

    decoded_body = raw_body.decode(charset)
    parsed_body = json.loads(decoded_body)

    timestamp = requested_at.strftime("%Y%m%dT%H%M%SZ")
    query_name = safe_filename(args.query)
    file_prefix = (
        f"{timestamp}_{query_name}_{args.language}_{args.country}"
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)

    raw_path = args.output_dir / f"{file_prefix}.body.bin"
    parsed_path = args.output_dir / f"{file_prefix}.parsed.json"
    metadata_path = args.output_dir / f"{file_prefix}.metadata.json"

    raw_path.write_bytes(raw_body)

    parsed_path.write_text(
        json.dumps(parsed_body, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    metadata = {
        "requested_at": requested_at.isoformat(),
        "request_url": request_url,
        "request_parameters": parameters,
        "http_status_code": status_code,
        "content_type": content_type,
        "charset": charset,
        "response_headers": response_headers,
    }

    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    request_id = None
    suggestion_count = None

    if args.save_to_database:
        database_url = os.environ.get("YOUTUBE_DATABASE_URL")

        if not database_url:
            raise RuntimeError(
                "YOUTUBE_DATABASE_URL must be set "
                "when --save-to-database is used."
            )

        request_id = insert_raw_autocomplete_request(
            database_url=database_url,
            requested_at=requested_at,
            requested_query=args.query,
            requested_language=args.language,
            requested_country=args.country,
            endpoint_url=BASE_URL,
            request_parameters=parameters,
            http_status_code=status_code,
            response_content_type=content_type,
            response_charset=charset,
            response_headers=response_headers,
            response_body=raw_body,
        )

        normalized_response = parse_autocomplete_response(
            raw_body=raw_body,
            charset=charset,
        )

        suggestion_count = upsert_autocomplete_suggestions(
            database_url=database_url,
            request_id=request_id,
            suggestions=normalized_response["suggestions"],
        )

    if request_id is not None:
        print(f"Saved to database with request_id: {request_id}")
    
    if suggestion_count is not None:
        print(f"Saved staging suggestions: {suggestion_count}")
    print(f"HTTP status: {status_code}")
    print(f"Content-Type: {content_type}")
    print(f"Charset: {charset}")
    print(f"Raw response: {raw_path}")
    print(f"Parsed response: {parsed_path}")
    print(f"Metadata: {metadata_path}")
    print(f"SHA-256: {response_sha256}")
    print()
    print(json.dumps(parsed_body, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()