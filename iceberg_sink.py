import mysql.connector
import pyarrow as pa
from pyiceberg.catalog.sql import SqlCatalog
from datetime import datetime
import os
from dotenv import load_dotenv
import time

load_dotenv()

WAREHOUSE_PATH = os.path.abspath("iceberg_warehouse")

catalog = SqlCatalog(
    "local",
    **{
        "uri"      : "sqlite:///iceberg_catalog.db",
        "warehouse": f"file://{WAREHOUSE_PATH}",
    }
)

table = catalog.load_table("movielens.ratings")
print("Iceberg table loaded!")

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "movielens")
)

cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM ratings")
total = cursor.fetchone()[0]
print(f"Total ratings in MySQL: {total:,}")

# Mỗi batch append tạo ra 1 snapshot trong Iceberg
BATCH_SIZE = 100_000
offset    = 0
batch_num = 0

arrow_schema = pa.schema([
    pa.field("user_id",   pa.int32(), nullable=False),
    pa.field("movie_id",  pa.int32(), nullable=False),
    pa.field("rating",    pa.int32(), nullable=False),
    pa.field("timestamp", pa.int64(), nullable=False),
])

while offset < total:
    batch_num += 1

    cursor.execute(f"""
        SELECT user_id, movie_id, rating, timestamp
        FROM ratings
        LIMIT {BATCH_SIZE} OFFSET {offset}
    """)
    rows = cursor.fetchall()

    if not rows:
        break

    arrow_table = pa.table(
        {
            "user_id"  : pa.array([r[0] for r in rows], type=pa.int32()),
            "movie_id" : pa.array([r[1] for r in rows], type=pa.int32()),
            "rating"   : pa.array([r[2] for r in rows], type=pa.int32()),
            "timestamp": pa.array([r[3] for r in rows], type=pa.int64()),
        },
        schema=arrow_schema
    )

    table.append(arrow_table)

    offset += len(rows)
    snapshot_id = table.current_snapshot().snapshot_id

    print(f"  Batch {batch_num}: wrote {len(rows):>7,} rows | "
          f"Total: {offset:>9,}/{total:,} | "
          f"Snapshot: {snapshot_id}")

    time.sleep(0.5)

cursor.close()
conn.close()

print(f"\n{'='*60}")
print(f"📸 ICEBERG SNAPSHOTS")
print(f"{'='*60}")
print(f"{'#':<5} {'Snapshot ID':<22} {'Rows Added':<15} {'Timestamp'}")
print(f"{'-'*60}")

for i, snap in enumerate(table.snapshots(), 1):
    added = snap.summary.get("added-records", "?")
    dt    = datetime.fromtimestamp(snap.timestamp_ms / 1000).strftime("%H:%M:%S")
    print(f"{i:<5} {snap.snapshot_id:<22} {str(added):<15} {dt}")

print(f"\nCurrent snapshot: {table.current_snapshot().snapshot_id}")
print(f"\nSink completed!")
