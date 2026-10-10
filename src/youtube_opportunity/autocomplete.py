import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


BASE_URL = "https://suggestqueries.google.com/complete/search"


@dataclass(frozen=True)
class AutocompleteHttpResponse:
    requested_at: datetime
    endpoint_url: str
    request_parameters: dict[str, str]
    status_code: int
    content_type: str
    charset: str
    headers: dict[str, str]
    body: bytes


def fetch_autocomplete_response(
    *,
    query: str,
    language: str = "tr",
    country: str = "TR",
    timeout_seconds: int = 30,
) -> AutocompleteHttpResponse:
    parameters = {
        "client": "firefox",
        "ds": "yt",
        "hl": language,
        "gl": country,
        "q": query,
    }

    request_url = f"{BASE_URL}?{urlencode(parameters)}"

    request = Request(
        request_url,
        headers={
            "User-Agent": "youtube-opportunity-finder/0.1",
        },
    )

    requested_at = datetime.now(timezone.utc)

    with urlopen(request, timeout=timeout_seconds) as response:
        body = response.read()

        return AutocompleteHttpResponse(
            requested_at=requested_at,
            endpoint_url=BASE_URL,
            request_parameters=parameters,
            status_code=response.status,
            content_type=response.headers.get_content_type(),
            charset=(
                response.headers.get_content_charset()
                or "utf-8"
            ),
            headers=dict(response.headers.items()),
            body=body,
        )

class SourceContractError(ValueError):
    """Raised when autocomplete returns an unexpected structure."""


def parse_autocomplete_response(
    raw_body: bytes,
    charset: str,
) -> dict[str, Any]:
    decoded_body = raw_body.decode(charset)
    payload = json.loads(decoded_body)

    if not isinstance(payload, list) or len(payload) < 2:
        raise SourceContractError(
            "Expected a list containing query and suggestions."
        )

    echoed_query = payload[0]
    suggestions = payload[1]

    if not isinstance(echoed_query, str):
        raise SourceContractError("Echoed query must be a string.")

    if not isinstance(suggestions, list) or not all(
        isinstance(item, str) for item in suggestions
    ):
        raise SourceContractError(
            "Suggestions must be a list of strings."
        )

    metadata = (
        payload[3]
        if len(payload) > 3 and isinstance(payload[3], dict)
        else {}
    )

    subtype_groups = metadata.get("google:suggestsubtypes", [])

    records = []

    for position, suggestion in enumerate(suggestions):
        subtype_codes = (
            subtype_groups[position]
            if position < len(subtype_groups)
            and isinstance(subtype_groups[position], list)
            else []
        )

        records.append(
            {
                "suggestion_position": position,
                "echoed_query": echoed_query,
                "suggestion_text": suggestion,
                "subtype_codes": subtype_codes,
            }
        )

    return {
        "echoed_query": echoed_query,
        "suggestions": records,
    }