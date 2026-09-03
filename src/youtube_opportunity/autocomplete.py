import json
from typing import Any


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