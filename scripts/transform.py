"""
transform.py

Reads the input CSV, translates the `subscribertype` field according to the
business mapping below, and writes the result as JSON (one JSON array, and
optionally newline-delimited JSON for Kafka publishing).

Mapping (per exercise spec):
    1 -> Prepaid
    2 -> Hybrid
    3 -> Postpaid

Usage:
    python transform.py --input data/Practice_sample.csv --output data/output.json
    python transform.py --input data/Practice_sample.csv --output data/output.ndjson --ndjson
"""

import argparse
import csv
import json
import sys
from pathlib import Path

SUBSCRIBER_TYPE_MAP = {
    "1": "Prepaid",
    "2": "Hybrid",
    "3": "Postpaid",
}


def transform_row(row: dict) -> dict:
    """Apply field translation to a single CSV row (dict)."""
    raw_value = str(row.get("subscribertype", "")).strip()
    row["subscribertype"] = SUBSCRIBER_TYPE_MAP.get(raw_value, raw_value)
    return row


def csv_to_records(input_path: Path) -> list:
    with open(input_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        return [transform_row(dict(row)) for row in reader]


def write_json(records: list, output_path: Path, ndjson: bool = False) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        if ndjson:
            for record in records:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
        else:
            json.dump(records, f, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Transform CSV to JSON with subscriber type translation")
    parser.add_argument("--input", required=True, help="Path to input CSV file")
    parser.add_argument("--output", required=True, help="Path to output JSON file")
    parser.add_argument("--ndjson", action="store_true", help="Write newline-delimited JSON (one record per line)")
    args = parser.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    records = csv_to_records(input_path)
    write_json(records, output_path, ndjson=args.ndjson)
    print(f"Transformed {len(records)} records -> {output_path}")


if __name__ == "__main__":
    main()
