"""
minio_upload.py

Creates (if needed) a MinIO bucket and uploads the transformed JSON output
file to it.

Usage:
    python minio_upload.py --input data/output.json --bucket subscribers-bucket \
        --endpoint localhost:9000 --access-key minioadmin --secret-key minioadmin
"""

import argparse
import sys
from pathlib import Path

from minio import Minio
from minio.error import S3Error


def main():
    parser = argparse.ArgumentParser(description="Upload a JSON file to a MinIO bucket")
    parser.add_argument("--input", required=True, help="Path to the JSON file to upload")
    parser.add_argument("--bucket", default="subscribers-bucket", help="Target MinIO bucket name")
    parser.add_argument("--object-name", default=None, help="Object name in the bucket (default: input filename)")
    parser.add_argument("--endpoint", default="localhost:9000", help="MinIO endpoint (host:port)")
    parser.add_argument("--access-key", default="minioadmin", help="MinIO access key")
    parser.add_argument("--secret-key", default="minioadmin", help="MinIO secret key")
    parser.add_argument("--secure", action="store_true", help="Use HTTPS")
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        print(f"ERROR: input file not found: {input_path}", file=sys.stderr)
        sys.exit(1)

    object_name = args.object_name or input_path.name

    client = Minio(
        args.endpoint,
        access_key=args.access_key,
        secret_key=args.secret_key,
        secure=args.secure,
    )

    try:
        if not client.bucket_exists(args.bucket):
            client.make_bucket(args.bucket)
            print(f"Created bucket '{args.bucket}'")
        else:
            print(f"Bucket '{args.bucket}' already exists")

        client.fput_object(
            bucket_name=args.bucket,
            object_name=object_name,
            file_path=str(input_path),
            content_type="application/json",
        )
        print(f"Uploaded '{input_path}' -> s3://{args.bucket}/{object_name}")

    except S3Error as exc:
        print(f"ERROR: MinIO S3 error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
