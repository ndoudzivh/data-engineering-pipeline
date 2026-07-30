# Data Engineering Practical Exercise

Implements the exercise brief: ingest a CSV with **Apache NiFi**, translate
`subscribertype` (1=Prepaid, 2=Hybrid, 3=Postpaid), convert to JSON, publish
to **Kafka**, and land the JSON file in **MinIO** — plus a GitHub Actions
**CI/CD** pipeline that automatically tests and validates the whole flow.

## Repository layout

```
.
├── docker-compose.yml          # NiFi + Kafka + Zookeeper + MinIO stack
├── data/
│   ├── Practice_sample.csv     # Input sample (NiFi's GetFile reads from here)
│   └── output.json             # Generated transformed output (git-ignored)
├── nifi/
│   └── README.md               # Step-by-step NiFi canvas flow instructions
├── scripts/                    # Python reference implementation of the same
│   │                           # pipeline, used for local testing + CI
│   ├── transform.py            # CSV -> JSON with subscribertype mapping
│   ├── kafka_producer.py       # Publish JSON records to a Kafka topic
│   ├── kafka_consumer.py       # Consume/verify records from Kafka
│   ├── minio_upload.py         # Create bucket + upload JSON to MinIO
│   └── requirements.txt
├── tests/
│   └── test_transform.py       # Unit tests for the transform logic
└── .github/workflows/
    └── ci-cd.yml                # CI/CD: test -> integration -> package
```

## Why both NiFi (GUI) and Python scripts?

Apache NiFi flows are built on a visual canvas, which doesn't lend itself to
automated CI testing directly. The Python scripts in `scripts/` implement
**the exact same transformation logic** (see `nifi/README.md` for the
processor-by-processor mapping) so that:

- the core business rule (subscriber type translation) is unit-testable,
- the end-to-end pipeline (produce → Kafka → consume, upload → MinIO) can be
  exercised automatically in GitHub Actions on every push/PR,
- you still get full marks on the NiFi deliverable by building the flow in
  the UI per `nifi/README.md` and demonstrating it against the same
  `docker-compose.yml` stack.

## Quick start (local, full stack)

```bash
# 1. Bring up NiFi, Kafka, Zookeeper, MinIO
docker compose up -d

# 2. Build the NiFi flow (see nifi/README.md), or run the Python equivalent:
pip install -r scripts/requirements.txt

python scripts/transform.py \
  --input data/Practice_sample.csv --output data/output.json

python scripts/kafka_producer.py \
  --input data/output.json --topic subscribers --bootstrap-servers localhost:29092

python scripts/kafka_consumer.py \
  --topic subscribers --bootstrap-servers localhost:29092 --max-messages 17 --timeout-ms 15000

python scripts/minio_upload.py \
  --input data/output.json --bucket subscribers-bucket \
  --endpoint localhost:9000 --access-key minioadmin --secret-key minioadmin

# 3. Verify
#    - NiFi UI:    https://localhost:8443/nifi
#    - MinIO UI:   http://localhost:9001  (minioadmin / minioadmin)
#    - Kafka topic: docker exec -it kafka kafka-console-consumer \
#                     --bootstrap-server localhost:9092 --topic subscribers --from-beginning
```

## CI/CD (GitHub Actions)

`.github/workflows/ci-cd.yml` runs on every push/PR to `main`:

1. **test** — installs dependencies, runs `pytest` unit tests against the
   transform logic, and does a smoke run of `transform.py` on the sample
   CSV, uploading the resulting JSON as a build artifact.
2. **integration** — spins up real Kafka + Zookeeper + MinIO service
   containers, runs the full produce → consume flow against Kafka, and
   uploads the transformed JSON to a MinIO bucket, failing the build if any
   step doesn't behave as expected.
3. **deploy** — on pushes to `main` only, packages `scripts/`, `nifi/`, and
   `docker-compose.yml` plus the validated JSON output into a versioned
   release artifact (`data-eng-pipeline-<sha>.tar.gz`).

### Setting this up on GitHub

```bash
git init
git add .
git commit -m "Data engineering practical exercise: NiFi, Kafka, MinIO, CI/CD"
git branch -M main
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

Once pushed, the workflow runs automatically — check the **Actions** tab in
your GitHub repo. No secrets are required since Kafka/MinIO credentials used
here are local defaults for the exercise; for a real deployment, move
`minioadmin`/`minioadmin` and any broker credentials into
**Settings → Secrets and variables → Actions**.

## Expected deliverables checklist (from the exercise brief)

- [x] CSV ingested via NiFi `GetFile` (see `nifi/README.md`)
- [x] `subscribertype` translated: 1→Prepaid, 2→Hybrid, 3→Postpaid
- [x] CSV converted to JSON (`ConvertRecord` in NiFi / `transform.py` in Python)
- [x] JSON records published to Kafka (`PublishKafka` / `kafka_producer.py`)
- [x] Kafka messages consumable via a consumer script (`kafka_consumer.py`)
- [x] Transformed JSON file uploaded to a MinIO bucket (`PutS3Object` / `minio_upload.py`)
- [x] CI/CD pipeline on GitHub Actions validating the above automatically
