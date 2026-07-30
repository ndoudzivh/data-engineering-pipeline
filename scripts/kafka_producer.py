"""
kafka_producer.py

Streams transformed JSON records to a Kafka topic, one message per record.

Usage:
    python kafka_producer.py --input data/output.json --topic subscribers \
        --bootstrap-servers localhost:29092
"""

import argparse
import json
import sys
from pathlib import Path

from kafka import KafkaProducer


def load_records(input_path: Path) -> list:
    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict):
        data = [data]
    return data


def main():
    parser = argparse.ArgumentParser(description="Publish JSON records to a Kafka topic")
    parser.add_argument("--input", required=True, help="Path to transformed JSON file")
    parser.add_argument("--topic", default="subscribers", help="Kafka topic name")
    parser.add_argument("--bootstrap-servers", default="localhost:29092", help="Kafka bootstrap servers")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    records = load_records(input_path)

    producer = KafkaProducer(
        bootstrap_servers=args.bootstrap_servers,
        value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        key_serializer=lambda k: str(k).encode("utf-8") if k is not None else None,
    )

    for record in records:
        key = record.get("ID")
        producer.send(args.topic, key=key, value=record)

    producer.flush()
    producer.close()
    print(f"Published {len(records)} records to topic '{args.topic}'")


if __name__ == "__main__":
    main()
