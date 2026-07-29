import base64
import os
from collections import OrderedDict
from enum import Enum
from pathlib import Path
from typing import Optional

from openai import APIConnectionError, APIStatusError, AuthenticationError, OpenAI, RateLimitError
from pydantic import BaseModel, Field


MAX_FILES = 6
MAX_FILE_SIZE = 12 * 1024 * 1024
MAX_TOTAL_SIZE = 25 * 1024 * 1024
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".pdf"}
MIME_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".pdf": "application/pdf",
}


class Broker(str, Enum):
    ZERODHA = "Zerodha"
    UPSTOX = "Upstox"
    OTHER = "Other"


class Sector(str, Enum):
    AUTOMOBILE = "Automobile"
    CONSUMER = "Consumer"
    ENERGY = "Energy"
    FINANCIALS = "Financials"
    HEALTHCARE = "Healthcare"
    INDUSTRIALS = "Industrials"
    TECHNOLOGY = "Technology"
    TELECOM = "Telecom"
    UTILITIES = "Utilities"
    OTHER = "Other"


class MarketCap(str, Enum):
    LARGE = "Large Cap"
    MID = "Mid Cap"
    SMALL = "Small Cap"
    UNKNOWN = "Unknown"


class ExtractedHolding(BaseModel):
    symbol: str = Field(description="Exchange symbol exactly as visible, normalized to uppercase")
    company: str = Field(description="Company name if visible or confidently known; otherwise repeat symbol")
    quantity: Optional[float] = Field(description="Visible holding quantity, never inferred")
    average_price: Optional[float] = Field(description="Visible average acquisition price per share")
    current_price: Optional[float] = Field(description="Visible current price or LTP per share")
    invested_value: Optional[float] = Field(description="Visible total invested value if present")
    sector: Sector = Field(description="Broad sector classification for verification")
    market_cap: MarketCap = Field(description="Best-effort market-cap category; Unknown if uncertain")
    confidence: float = Field(ge=0, le=1, description="Confidence that visible numeric fields were read correctly")
    source_number: int = Field(ge=1, description="One-based number of the uploaded source containing this row")
    warning: Optional[str] = Field(description="Short warning for missing, cropped, or uncertain values")


class PortfolioExtraction(BaseModel):
    broker: Broker
    holdings: list[ExtractedHolding]
    warnings: list[str]


class DocumentExtractionError(Exception):
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code


def _has_valid_signature(extension, data):
    if extension == ".pdf":
        return data.startswith(b"%PDF")
    if extension == ".png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")
    return data.startswith(b"\xff\xd8\xff")


def validate_uploads(files):
    if not files or not any(file.filename for file in files):
        raise DocumentExtractionError("Select at least one JPG, PNG, or PDF file.")
    if len(files) > MAX_FILES:
        raise DocumentExtractionError(f"Upload no more than {MAX_FILES} files at once.")

    prepared = []
    total_size = 0

    for file in files:
        filename = Path(file.filename or "").name
        extension = Path(filename).suffix.lower()
        if extension not in ALLOWED_EXTENSIONS:
            raise DocumentExtractionError(f"{filename} is not a supported JPG, PNG, or PDF file.")

        data = file.read()
        if not data:
            raise DocumentExtractionError(f"{filename} is empty.")
        if len(data) > MAX_FILE_SIZE:
            raise DocumentExtractionError(f"{filename} exceeds the 12 MB per-file limit.")
        if not _has_valid_signature(extension, data):
            raise DocumentExtractionError(f"{filename} does not match its file extension.")

        total_size += len(data)
        prepared.append({
            "filename": filename,
            "extension": extension,
            "mime_type": MIME_TYPES[extension],
            "data": data,
        })

    if total_size > MAX_TOTAL_SIZE:
        raise DocumentExtractionError("Uploads must be 25 MB or smaller in total.")
    return prepared


def _build_content(files):
    content = [{
        "type": "input_text",
        "text": (
            "Extract every portfolio holding visibly present in the supplied files. "
            "Files may be overlapping screenshots from the same portfolio."
        ),
    }]

    for index, file in enumerate(files, start=1):
        encoded = base64.b64encode(file["data"]).decode("ascii")
        content.append({
            "type": "input_text",
            "text": f"Source {index}: {file['filename']}",
        })
        if file["extension"] == ".pdf":
            content.append({
                "type": "input_file",
                "filename": file["filename"],
                "file_data": f"data:{file['mime_type']};base64,{encoded}",
                "detail": "high",
            })
        else:
            content.append({
                "type": "input_image",
                "image_url": f"data:{file['mime_type']};base64,{encoded}",
                "detail": "original",
            })
    return content


def _deduplicate_holdings(holdings):
    unique = OrderedDict()
    warnings = []

    for holding in holdings:
        key = holding.symbol.strip().upper().replace(" ", "")
        if not key:
            continue
        holding.symbol = key
        existing = unique.get(key)
        if existing is None:
            unique[key] = holding
            continue

        same_position = (
            existing.quantity == holding.quantity
            and existing.average_price == holding.average_price
        )
        if not same_position:
            warnings.append(
                f"Conflicting values were found for {key}; verify quantity and average price."
            )
        if holding.confidence > existing.confidence:
            unique[key] = holding

    return list(unique.values()), warnings


def _serialize_holding(holding, files):
    market_cap = holding.market_cap.value
    warning = holding.warning
    if market_cap == "Unknown":
        market_cap = ""
        warning = warning or "Market-cap category needs verification."

    return {
        "symbol": holding.symbol,
        "company": holding.company or holding.symbol,
        "quantity": holding.quantity if holding.quantity is not None else "",
        "average_price": holding.average_price if holding.average_price is not None else "",
        "current_price": holding.current_price if holding.current_price is not None else "",
        "sector": holding.sector.value,
        "market_cap": market_cap,
        "confidence": round(holding.confidence, 2),
        "warning": warning or "",
        "source_file": files[min(holding.source_number - 1, len(files) - 1)]["filename"],
    }


def extract_portfolio_documents(files):
    if not os.getenv("OPENAI_API_KEY"):
        raise DocumentExtractionError(
            "OPENAI_API_KEY is missing. Add it to backend/.env and restart Flask.",
            503,
        )

    instructions = """
You extract Indian equity portfolio holdings from Zerodha, Upstox, and generic broker screenshots or PDFs.

Rules:
- Read only holding rows visibly present. Never invent hidden, cropped, or off-screen holdings.
- A summary that says Holdings (9) does not mean nine rows should be returned; return only visible rows.
- Distinguish average acquisition price from LTP/current price, invested value, P&L, and percentage return.
- Indian comma formatting is numeric punctuation: 3,11,416.32 means 311416.32.
- Preserve quantities exactly. Never calculate quantity from approximate displayed totals when quantity is visible.
- Multiple sources may overlap. Return rows from all sources; server-side logic removes duplicates.
- Zerodha often shows 'Qty.', 'Avg.', 'Invested', and 'LTP'.
- Upstox often shows the symbol, 'Invested', 'Avg.', 'Qty.', and 'LTP' in separate aligned columns.
- Set source_number to the numbered source containing the holding.
- Use confidence below 0.85 and add a warning whenever digits are blurry, cropped, or ambiguous.
- Sector and market cap are best-effort classifications for user verification, not extracted facts.
""".strip()

    try:
        client = OpenAI()
        response = client.responses.parse(
            model=os.getenv("OPENAI_MODEL", "gpt-5.6"),
            reasoning={"effort": os.getenv("OPENAI_REASONING_EFFORT", "high")},
            instructions=instructions,
            input=[{"role": "user", "content": _build_content(files)}],
            text_format=PortfolioExtraction,
            store=False,
        )
        parsed = response.output_parsed
        if parsed is None:
            raise DocumentExtractionError("The AI could not extract a portfolio from these files.", 422)

        holdings, duplicate_warnings = _deduplicate_holdings(parsed.holdings)
        if not holdings:
            raise DocumentExtractionError(
                "No visible holding rows were found. Try a clearer, uncropped screenshot.",
                422,
            )

        return {
            "broker": parsed.broker.value,
            "holdings": [_serialize_holding(item, files) for item in holdings],
            "warnings": parsed.warnings + duplicate_warnings,
            "source_count": len(files),
            "model": os.getenv("OPENAI_MODEL", "gpt-5.6"),
        }
    except AuthenticationError as error:
        raise DocumentExtractionError("The OpenAI API key is invalid or inactive.", 401) from error
    except RateLimitError as error:
        raise DocumentExtractionError(
            "The OpenAI API quota or rate limit was reached. Check API billing and try again.",
            429,
        ) from error
    except APIConnectionError as error:
        raise DocumentExtractionError("Could not connect to the OpenAI API.", 502) from error
    except APIStatusError as error:
        raise DocumentExtractionError(f"OpenAI extraction failed with status {error.status_code}.", 502) from error
    except DocumentExtractionError:
        raise
    except Exception as error:
        raise DocumentExtractionError(
            "The file could not be processed. Try a clearer image or a text-based PDF.",
            502,
        ) from error
