import os
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.types import StringType
from datetime import datetime

WAREHOUSE_PATH = os.path.abspath("iceberg_warehouse")

catalog = SqlCatalog(
    "local",
    **{
        "uri"      : "sqlite:///iceberg_catalog.db",
        "warehouse": f"file://{WAREHOUSE_PATH}",
    }
)

table = catalog.load_table("movielens.ratings")

# Xem lịch sử các lần write
snapshots = table.snapshots()

print("=" * 65)
print("📸 ALL SNAPSHOTS (Version History)")
print("=" * 65)
print(f"{'#':<5} {'Snapshot ID':<25} {'Rows':<12} {'Time'}")
print("-" * 65)

for i, snap in enumerate(snapshots, 1):
    added = snap.summary.get("added-records", "?")
    dt    = datetime.fromtimestamp(snap.timestamp_ms / 1000).strftime("%H:%M:%S")
    print(f"{i:<5} {snap.snapshot_id:<25} {str(added):<12} {dt}")

print(f"\nCurrent snapshot : {table.current_snapshot().snapshot_id}")
print(f"Total snapshots  : {len(snapshots)}")

# Query toàn bộ data hiện tại
print("\n" + "=" * 65)
print("📊 CURRENT DATA (latest snapshot)")
print("=" * 65)

df = table.scan().to_arrow()
ratings_list = df["rating"].to_pylist()
avg = sum(ratings_list) / len(ratings_list)

print(f"Total rows  : {len(df):,}")
print(f"Avg rating  : {avg:.4f}")
print(f"Min rating  : {min(ratings_list)}")
print(f"Max rating  : {max(ratings_list)}")

# Time travel:
if len(snapshots) >= 2:
    print("\n" + "=" * 65)
    print("⏱️  TIME TRAVEL — Query snapshot đầu tiên")
    print("=" * 65)

    first_snap = snapshots[0]
    dt_first   = datetime.fromtimestamp(
        first_snap.timestamp_ms / 1000
    ).strftime("%H:%M:%S")

    print(f"Snapshot ID : {first_snap.snapshot_id}")
    print(f"Time        : {dt_first}")

    df_old      = table.scan(snapshot_id=first_snap.snapshot_id).to_arrow()
    old_ratings = df_old["rating"].to_pylist()

    print(f"Rows at that point : {len(df_old):,}")
    print(f"Avg rating         : {sum(old_ratings)/len(old_ratings):.4f}")
    print(f"\n✅ Data grew from {len(df_old):,} → {len(df):,} rows")
    print(f"   across {len(snapshots)} snapshots")

# Schema evolution
print("\n" + "=" * 65)
print("🔄 SCHEMA EVOLUTION — Thêm cột 'source'")
print("=" * 65)

print(f"Schema trước:")
print(table.schema())

existing_fields = [f.name for f in table.schema().fields]
if "source" not in existing_fields:
    with table.update_schema() as update:
        update.add_column("source", StringType())
    print("✅ Cột 'source' đã được thêm!")
else:
    print("ℹ️  Cột 'source' đã tồn tại từ trước")

table = catalog.load_table("movielens.ratings")
print(f"\nSchema sau:")
print(table.schema())
print("\n✅ Data cũ vẫn đọc được bình thường!")
