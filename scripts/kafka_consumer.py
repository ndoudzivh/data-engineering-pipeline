"""
kafka_consumer.py

Consumes and prints JSON records from a Kafka topic. Used to demonstrate /
verify that records published by kafka_producer.py were successfully
streamed through Kafka.

Usage:
    python kafka_consumer.py --topic subscribers --bootstrap-servers localhost:29092

    # Read a fixed number of messages then exit (useful for CI smoke tests):
    python kafka_consumer.py --topic subscribers --max-messages 17 --timeout-ms 15000
"""

import argparse
import json

from kafka import KafkaConsumer


def main():
    parser = argparse.ArgumentParser(description="Consume JSON records from a Kafka topic")
    parser.add_argument("--topic", default="subscribers", help="Kafka topic name")
    parser.add_argument("--bootstrap-servers", default="localhost:29092", help="Kafka bootstrap servers")
    parser.add_argument("--group-id", default="subscribers-consumer-group", help="Consumer group id")
    parser.add_argument("--from-beginning", action="store_true", default=True,
                         help="Read from the earliest offset (default: True)")
    parser.add_argument("--max-messages", type=int, default=None,
                         help="Exit after consuming this many messages (default: run until timeout)")
    parser.add_argument("--timeout-ms", type=int, default=10000,
                         help="Stop polling after this many ms of inactivity")
    args = parser.parse_args()

    consumer = KafkaConsumer(
        args.topic,
        bootstrap_servers=args.bootstrap_servers,
        group_id=args.group_id,
        auto_offset_reset="earliest" if args.from_beginning else "latest",
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        consumer_timeout_ms=args.timeout_ms,
    )

    count = 0
    for message in consumer:
        print(f"key={message.key} value={json.dumps(message.value)}")
        count += 1
        if args.max_messages and count >= args.max_messages:
            break

    consumer.close()
    print(f"Consumed {count} message(s) from topic '{args.topic}'")


if __name__ == "__main__":
    main()
