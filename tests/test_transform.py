import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from transform import transform_row, csv_to_records, SUBSCRIBER_TYPE_MAP  # noqa: E402

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SAMPLE_CSV = DATA_DIR / "Practice_sample.csv"


def test_subscriber_type_mapping():
    assert transform_row({"subscribertype": "1"})["subscribertype"] == "Prepaid"
    assert transform_row({"subscribertype": "2"})["subscribertype"] == "Hybrid"
    assert transform_row({"subscribertype": "3"})["subscribertype"] == "Postpaid"


def test_unknown_subscriber_type_passthrough():
    # Unmapped values should pass through unchanged rather than crash
    assert transform_row({"subscribertype": "9"})["subscribertype"] == "9"


def test_csv_to_records_translates_all_rows():
    assert SAMPLE_CSV.exists(), "sample CSV fixture is missing"
    records = csv_to_records(SAMPLE_CSV)
    assert len(records) > 0
    valid_values = set(SUBSCRIBER_TYPE_MAP.values())
    for record in records:
        assert record["subscribertype"] in valid_values


def test_records_are_json_serializable():
    records = csv_to_records(SAMPLE_CSV)
    # Should not raise
    json.dumps(records)
