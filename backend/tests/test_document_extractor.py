import io
import unittest

from pydantic import ValidationError
from werkzeug.datastructures import FileStorage

from services.document_extractor import (
    DocumentExtractionError,
    ExtractedHolding,
    _deduplicate_holdings,
    validate_uploads,
)


class DocumentExtractorTest(unittest.TestCase):
    def make_file(self, filename, data):
        return FileStorage(stream=io.BytesIO(data), filename=filename)

    def test_accepts_png_signature(self):
        files = [self.make_file("portfolio.png", b"\x89PNG\r\n\x1a\nimage")]
        prepared = validate_uploads(files)

        self.assertEqual(prepared[0]["mime_type"], "image/png")

    def test_rejects_file_with_fake_extension(self):
        files = [self.make_file("portfolio.pdf", b"not a pdf")]

        with self.assertRaises(DocumentExtractionError):
            validate_uploads(files)

    def test_deduplicates_overlapping_screenshots(self):
        first = ExtractedHolding(
            symbol="CDSL",
            company="CDSL",
            quantity=20,
            average_price=1764.30,
            current_price=1173.25,
            invested_value=35286,
            sector="Financials",
            market_cap="Mid Cap",
            confidence=0.91,
            source_number=1,
            warning=None,
        )
        second = first.model_copy(update={"confidence": 0.97, "source_number": 2})
        holdings, warnings = _deduplicate_holdings([first, second])

        self.assertEqual(len(holdings), 1)
        self.assertEqual(holdings[0].confidence, 0.97)
        self.assertEqual(warnings, [])

    def test_confidence_must_be_between_zero_and_one(self):
        with self.assertRaises(ValidationError):
            ExtractedHolding(
                symbol="IRCON",
                company="IRCON",
                quantity=100,
                average_price=234.33,
                current_price=155.42,
                invested_value=23433,
                sector="Industrials",
                market_cap="Mid Cap",
                confidence=2,
                source_number=1,
                warning=None,
            )


if __name__ == "__main__":
    unittest.main()
