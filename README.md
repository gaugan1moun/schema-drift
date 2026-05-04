# schema-drift

> Detect and report schema changes across database migrations over time.

---

## Installation

```bash
pip install schema-drift
```

---

## Usage

```python
from schema_drift import SchemaDriftDetector

detector = SchemaDriftDetector(db_url="postgresql://user:password@localhost/mydb")

# Capture a baseline snapshot
detector.snapshot(label="v1.0")

# After running migrations, compare against the baseline
report = detector.compare(baseline="v1.0")

# Print a summary of detected changes
report.summary()
# Output:
# [ADDED]   users.last_login (timestamp)
# [REMOVED] orders.legacy_id (integer)
# [CHANGED] products.price  varchar(50) -> numeric(10, 2)
```

You can also export the report to JSON or HTML:

```python
report.export("drift_report.json", format="json")
report.export("drift_report.html", format="html")
```

---

## Supported Databases

- PostgreSQL
- MySQL / MariaDB
- SQLite

---

## Configuration

Set options via a config file or environment variables:

```bash
export SCHEMA_DRIFT_DB_URL="postgresql://user:password@localhost/mydb"
export SCHEMA_DRIFT_SNAPSHOT_DIR="./snapshots"
```

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Contributing

Pull requests are welcome. Please open an issue first to discuss any major changes.