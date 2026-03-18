"""TKPI CSV import service — shared parsing, validation, and DB write logic.

Used by both:
  - CLI: scripts/import_tkpi.py
  - API: endpoints/admin_tkpi_import.py

CSV Contract:
  Encoding: UTF-8 (BOM handled)
  Delimiter: auto-detect comma (,) or semicolon (;)
  Decimals: dot (0.3) and comma (0,3) supported
  Thousand separators: NOT supported — "1.234,5" is detected and rejected as ERROR.

Validation:
  ERROR → row skipped: empty tkpi_code, empty name, negative, unparsable
  WARNING → row accepted: energi_kal==0, all macros==0 (unless "air")

NULL: all nutrition columns are nullable — empty → NULL.
"""

import csv
import io
import re
import logging
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

from sqlalchemy import text, select, func
from sqlalchemy.orm import Session

from app.models.tkpi_food import TKPIFood

logger = logging.getLogger(__name__)

BATCH_SIZE = 500
MAX_REPORT_ITEMS = 200

NUMERIC_FIELDS = ["energi_kal", "protein_g", "lemak_g", "karbo_g", "serat_g"]
REQUIRED_COLUMNS = {"tkpi_code", "name"}

UPSERT_SQL = text("""
    INSERT INTO tkpi_foods (tkpi_code, name, energi_kal, protein_g, lemak_g, karbo_g, serat_g)
    VALUES (:tkpi_code, :name, :energi_kal, :protein_g, :lemak_g, :karbo_g, :serat_g)
    ON CONFLICT (tkpi_code) DO UPDATE SET
        name       = EXCLUDED.name,
        energi_kal = EXCLUDED.energi_kal,
        protein_g  = EXCLUDED.protein_g,
        lemak_g    = EXCLUDED.lemak_g,
        karbo_g    = EXCLUDED.karbo_g,
        serat_g    = EXCLUDED.serat_g
""")


# ── Data Classes ─────────────────────────────────────────────────────────

@dataclass
class ImportResult:
    """Result container for TKPI CSV import."""
    dry_run: bool = True
    filename: str = ""
    rows_total: int = 0
    processed_count: int = 0
    inserted_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    skipped_blank_rows: int = 0
    warnings_count: int = 0
    errors_count: int = 0
    existing_count: int = 0   # how many valid rows matched existing tkpi_codes
    new_count: int = 0        # how many valid rows are new tkpi_codes
    warnings: list = field(default_factory=list)
    errors: list = field(default_factory=list)
    errors_truncated: bool = False
    warnings_truncated: bool = False

    def to_dict(self) -> dict:
        return {
            "dry_run": self.dry_run,
            "filename": self.filename,
            "rows_total": self.rows_total,
            "processed_count": self.processed_count,
            "inserted_count": self.inserted_count,
            "updated_count": self.updated_count,
            "existing_count": self.existing_count,
            "new_count": self.new_count,
            "skipped_count": self.skipped_count,
            "skipped_blank_rows": self.skipped_blank_rows,
            "warnings_count": self.warnings_count,
            "errors_count": self.errors_count,
            "warnings": self.warnings[:MAX_REPORT_ITEMS],
            "errors": self.errors[:MAX_REPORT_ITEMS],
            "errors_truncated": self.errors_truncated,
            "warnings_truncated": self.warnings_truncated,
        }

    def audit_meta(self) -> dict:
        """Generate audit log metadata."""
        # Summarize top error reasons
        error_reasons = Counter(e["message"] for e in self.errors)
        top_reasons = dict(error_reasons.most_common(10))

        return {
            "filename": self.filename,
            "dry_run": self.dry_run,
            "rows_total": self.rows_total,
            "processed_count": self.processed_count,
            "inserted_count": self.inserted_count,
            "updated_count": self.updated_count,
            "skipped_count": self.skipped_count,
            "errors_count": self.errors_count,
            "warnings_count": self.warnings_count,
            "top_skip_reasons": top_reasons,
        }


# ── Parsing Helpers ──────────────────────────────────────────────────────

def detect_delimiter_from_text(text_content: str) -> str:
    """Auto-detect CSV delimiter from first line of text."""
    first_line = text_content.split("\n", 1)[0]
    try:
        dialect = csv.Sniffer().sniff(first_line, delimiters=",;")
        return dialect.delimiter
    except csv.Error:
        if first_line.count(";") > first_line.count(","):
            return ";"
        return ","


def detect_delimiter_from_file(file_path) -> str:
    """Auto-detect CSV delimiter from first line of a file on disk."""
    with open(file_path, encoding="utf-8-sig") as f:
        first_line = f.readline()
    try:
        dialect = csv.Sniffer().sniff(first_line, delimiters=",;")
        return dialect.delimiter
    except csv.Error:
        if first_line.count(";") > first_line.count(","):
            return ";"
        return ","


# Regex: detect thousand-separator patterns like "1.234,5" or "1,234.5"
_THOUSAND_SEP_RE = re.compile(r'^\d{1,3}[.,]\d{3}[.,]')


def parse_float(value: str, field_name: str) -> tuple[Optional[float], Optional[str]]:
    """Parse numeric string to float.

    Returns (value, error_message).
    - Empty → (None, None)
    - Valid → (float, None)
    - Thousand-separator detected → (None, error)
    - Negative → (None, error)
    - Unparsable → (None, error)
    """
    if not value or not value.strip():
        return None, None

    trimmed = value.strip()

    # Guard: detect thousand-separator patterns (e.g. "1.234,5" or "1,234.5")
    if _THOUSAND_SEP_RE.match(trimmed):
        return None, (
            f"suspected thousand-separator format '{trimmed}' in {field_name}; "
            f"use plain numbers like 1234.5 or 1234,5"
        )

    cleaned = trimmed.replace(",", ".")
    try:
        result = float(cleaned)
    except ValueError:
        return None, f"unparsable numeric '{trimmed}' in {field_name}"

    if result < 0:
        return None, f"negative value {result} in {field_name}"

    return result, None


def normalize_name(name: str) -> str:
    """Trim and collapse double spaces."""
    return re.sub(r"\s+", " ", name.strip())


def check_warnings(record: dict) -> list[str]:
    """Check for suspicious-but-valid data."""
    warnings = []
    name_lower = record["name"].lower()

    if record.get("energi_kal") is not None and record["energi_kal"] == 0:
        if "air" not in name_lower:
            warnings.append("energi_kal == 0 (suspicious for non-water item)")

    macros = [record.get(f) for f in ("protein_g", "lemak_g", "karbo_g")]
    if all(v is not None and v == 0 for v in macros):
        if "air" not in name_lower:
            warnings.append("protein+lemak+karbo all == 0 (suspicious)")

    return warnings


# ── Row Parsing ──────────────────────────────────────────────────────────

def parse_row(raw_row: dict, row_num: int) -> tuple[Optional[dict], Optional[dict], list[dict]]:
    """Parse and validate a single CSV row.

    Returns (record, error, warnings_list).
    - record: dict ready for DB insert, or None if error
    - error: dict {row_number, tkpi_code, message} or None
    - warnings_list: list of warning dicts
    """
    row = {k.strip().lower(): v for k, v in raw_row.items()}

    # Detect fully blank rows (all fields empty/whitespace)
    if all(not (v or "").strip() for v in row.values()):
        return "BLANK", None, []

    tkpi_code = (row.get("tkpi_code") or "").strip().upper()
    if not tkpi_code:
        return None, {"row_number": row_num, "tkpi_code": None, "message": "empty tkpi_code"}, []

    name = normalize_name(row.get("name") or "")
    if not name:
        return None, {"row_number": row_num, "tkpi_code": tkpi_code, "message": "empty name"}, []

    record = {"tkpi_code": tkpi_code, "name": name}

    for fld in NUMERIC_FIELDS:
        raw_val = row.get(fld, "")
        parsed, err = parse_float(raw_val, fld)
        if err:
            return None, {"row_number": row_num, "tkpi_code": tkpi_code, "message": err}, []
        record[fld] = parsed

    row_warnings = []
    for msg in check_warnings(record):
        row_warnings.append({"row_number": row_num, "tkpi_code": tkpi_code, "message": msg})

    return record, None, row_warnings


# ── Core Import Logic ────────────────────────────────────────────────────

def import_csv_from_text(
    csv_text: str,
    db: Session,
    *,
    filename: str = "",
    dry_run: bool = True,
) -> ImportResult:
    """Parse and optionally import TKPI CSV data.

    Args:
        csv_text: Full CSV content as string (UTF-8).
        db: SQLAlchemy session.
        filename: Original filename for reporting.
        dry_run: If True, parse/validate only, no DB writes.

    Returns:
        ImportResult with counts, errors, warnings.
    """
    result = ImportResult(dry_run=dry_run, filename=filename)

    # Detect delimiter
    delimiter = detect_delimiter_from_text(csv_text)
    logger.info(f"TKPI import: delimiter='{delimiter}', dry_run={dry_run}, file={filename}")

    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_text), delimiter=delimiter)

    # Validate headers
    if not reader.fieldnames:
        result.errors.append({"row_number": 0, "tkpi_code": None, "message": "CSV has no headers"})
        result.errors_count = 1
        return result

    headers = {h.strip().lower() for h in reader.fieldnames}
    missing = REQUIRED_COLUMNS - headers
    if missing:
        result.errors.append({
            "row_number": 0, "tkpi_code": None,
            "message": f"missing required columns: {sorted(missing)}"
        })
        result.errors_count = 1
        return result

    # If not dry-run, pre-fetch existing tkpi_codes for insert/update counting
    existing_codes: set = set()
    if not dry_run:
        rows = db.execute(
            select(TKPIFood.tkpi_code).where(TKPIFood.tkpi_code.isnot(None))
        ).scalars().all()
        existing_codes = {code.upper() for code in rows}

    valid_records: list[dict] = []

    for row_num, raw_row in enumerate(reader, start=2):
        result.rows_total += 1

        record, error, warnings = parse_row(raw_row, row_num)

        # Skip fully blank rows silently
        if record == "BLANK":
            result.skipped_blank_rows += 1
            continue

        if error:
            result.errors.append(error)
            result.errors_count += 1
            result.skipped_count += 1
            continue

        for w in warnings:
            result.warnings.append(w)
            result.warnings_count += 1

        valid_records.append(record)
        result.processed_count += 1

    # Truncation flags
    if result.errors_count > MAX_REPORT_ITEMS:
        result.errors_truncated = True
    if result.warnings_count > MAX_REPORT_ITEMS:
        result.warnings_truncated = True

    if dry_run:
        # Dry-run: estimate insert vs update by checking existing codes
        if not existing_codes:
            # Fetch for estimation even in dry-run
            rows = db.execute(
                select(TKPIFood.tkpi_code).where(TKPIFood.tkpi_code.isnot(None))
            ).scalars().all()
            existing_codes = {code.upper() for code in rows}

        for rec in valid_records:
            if rec["tkpi_code"] in existing_codes:
                result.updated_count += 1
                result.existing_count += 1
            else:
                result.inserted_count += 1
                result.new_count += 1

        logger.info(
            f"TKPI dry-run: {result.inserted_count} would insert, "
            f"{result.updated_count} would update, "
            f"{result.skipped_count} skipped, "
            f"{result.errors_count} errors, {result.warnings_count} warnings"
        )
    else:
        # Commit: execute upserts in batches
        inserted = 0
        updated = 0
        batch: list[dict] = []

        for rec in valid_records:
            is_update = rec["tkpi_code"] in existing_codes
            batch.append(rec)

            if is_update:
                updated += 1
                result.existing_count += 1
            else:
                inserted += 1
                result.new_count += 1
                # Track for subsequent rows in same batch
                existing_codes.add(rec["tkpi_code"])

            if len(batch) >= BATCH_SIZE:
                _flush_batch(db, batch)
                batch.clear()

        if batch:
            _flush_batch(db, batch)

        result.inserted_count = inserted
        result.updated_count = updated

        logger.info(
            f"TKPI commit: {inserted} inserted, {updated} updated, "
            f"{result.skipped_count} skipped, "
            f"{result.errors_count} errors, {result.warnings_count} warnings"
        )

    return result


def _flush_batch(db: Session, batch: list[dict]) -> None:
    """Execute upsert for a batch and commit."""
    for record in batch:
        db.execute(UPSERT_SQL, record)
    db.commit()
