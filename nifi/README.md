# Apache NiFi Flow — Build Instructions

NiFi flows are built visually on the canvas, so rather than a fragile
hand-authored `flow.xml.gz`, follow these steps in the NiFi UI
(`https://localhost:8443/nifi`, user `admin`, password from
`docker-compose.yml`). This mirrors exactly what `scripts/transform.py`,
`kafka_producer.py`, and `minio_upload.py` do in code, so you can cross-check
output at each stage.

## Processor chain

```
GetFile  ->  ConvertRecord (CSV -> JSON)  ->  UpdateRecord (map subscribertype)  ->  PublishKafka  ->  PutS3Object (MinIO)
                                                                                   \-> PutFile (optional local copy)
```

## 1. GetFile — read CSV from input directory
- Add processor `GetFile`.
- Properties:
  - `Input Directory`: `/opt/nifi/input` (mapped to `./data` on the host via docker-compose)
  - `File Filter`: `.*\.csv`
  - `Keep Source File`: `true` (so re-runs don't delete your sample)

## 2. ConvertRecord — CSV to JSON
- Add processor `ConvertRecord`.
- Create a `CSVReader` controller service:
  - `Schema Access Strategy`: `Use String Fields From Header` (uses the CSV header row directly — no Avro schema needed)
- Create a `JsonRecordSetWriter` controller service:
  - `Schema Write Strategy`: `Do Not Write Schema`
  - `Output Grouping`: `One Line Per Object` (produces newline-delimited JSON, ideal for streaming each record to Kafka as its own message)
- Enable both controller services, then set them as the Record Reader / Record Writer on `ConvertRecord`.

## 3. UpdateRecord — translate `subscribertype`
- Add processor `UpdateRecord`, using the same `CSVReader`-derived schema logic via a `JsonTreeReader` (since input is now JSON) and the same `JsonRecordSetWriter`.
- Set `Replacement Value Strategy`: `Record Path Value`.
- Add a dynamic property:
  - Property name: `/subscribertype`
  - Property value (RecordPath, chained `replace` expressions):
    ```
    replace(replace(replace(/subscribertype, '1', 'Prepaid'), '2', 'Hybrid'), '3', 'Postpaid')
    ```
  - This matches `SUBSCRIBER_TYPE_MAP` in `scripts/transform.py`.

## 4. PublishKafka (PublishKafka_2_6 or newer)
- `Kafka Brokers`: `kafka:9092` (the internal docker-compose service name/port)
- `Topic Name`: `subscribers`
- `Use Transactions`: `false` (fine for this exercise)
- `Delivery Guarantee`: `Guarantee Single Node`
- Connect success relationship onward; connect failure back to itself or to a `LogAttribute` for troubleshooting.

## 5. PutS3Object (used against MinIO, which is S3-compatible)
- `Object Key`: `${filename}` or a fixed name like `subscribers-transformed.json`
- `Bucket`: `subscribers-bucket`
- `Endpoint Override URL`: `http://minio:9000`
- `Access Key ID` / `Secret Access Key`: `minioadmin` / `minioadmin`
- `Region`: `us-east-1` (arbitrary — MinIO ignores this but the property is required)
- Enable **Path Style Access** in the AWS Credentials/Client properties (required for MinIO).

## 6. (Optional) PutFile
- Write a local copy of the transformed JSON to `/opt/nifi/output` for manual inspection, mirroring `data/output.json` from the Python path.

## Verifying the flow
1. Drop `Practice_sample.csv` into `./data` (already there).
2. Start `GetFile` and downstream processors.
3. Check MinIO console at `http://localhost:9001` (login `minioadmin`/`minioadmin`) — the object should appear in `subscribers-bucket`.
4. Consume the Kafka topic to confirm messages arrived:
   ```
   python scripts/kafka_consumer.py --topic subscribers --bootstrap-servers localhost:29092 --max-messages 17 --timeout-ms 15000
   ```
   or via NiFi's own `ConsumeKafka` processor / the `kafka-console-consumer` CLI inside the `kafka` container:
   ```
   docker exec -it kafka kafka-console-consumer --bootstrap-server localhost:9092 --topic subscribers --from-beginning
   ```

## Exporting the flow for the repo
Once built and verified in the UI, export it as a versioned flow definition
for source control:
- Right-click the process group → **Download flow definition** (NiFi 1.16+), or
- Use NiFi Registry if you have it configured, and commit the resulting
  `flow.json`/`flow.xml.gz` into `nifi/exported-flow/` so it's reproducible
  in CI/CD (see `.github/workflows/ci-cd.yml`).
