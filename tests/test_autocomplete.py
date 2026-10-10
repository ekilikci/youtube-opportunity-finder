import unittest
from pathlib import Path

from youtube_opportunity.autocomplete import (
    SourceContractError,
    parse_autocomplete_response,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "autocomplete_python_tr_TR.body.bin"
)


class ParseAutocompleteResponseTest(unittest.TestCase):
    def test_parses_real_turkish_response(self) -> None:
        raw_body = FIXTURE_PATH.read_bytes()

        result = parse_autocomplete_response(
            raw_body=raw_body,
            charset="iso-8859-9",
        )

        self.assertEqual(result["echoed_query"], "python")
        self.assertEqual(len(result["suggestions"]), 10)

        first_suggestion = result["suggestions"][0]

        self.assertEqual(first_suggestion["suggestion_position"], 0)
        self.assertEqual(
            first_suggestion["suggestion_text"],
            "python dersleri",
        )
        self.assertEqual(first_suggestion["subtype_codes"], [512, 433])
        fourth_suggestion = result["suggestions"][3]
        fifth_suggestion = result["suggestions"][4]

        self.assertEqual(
            fourth_suggestion["suggestion_text"],
            "python nasıl indirilir",
        )

        self.assertEqual(
            fifth_suggestion["suggestion_text"],
            "python'a giriş",
        )

    def test_rejects_unexpected_source_contract(self) -> None:
        with self.assertRaises(SourceContractError):
            parse_autocomplete_response(
                raw_body=b'{"unexpected": "object"}',
                charset="utf-8",
            )


if __name__ == "__main__":
    unittest.main()