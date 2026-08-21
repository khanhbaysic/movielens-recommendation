import os
from pyiceberg.catalog.sql import SqlCatalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    NestedField, IntegerType, LongType, FloatType, StringType, TimestampType
)
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import BucketTransform

WAREHOUSE_PATH = os.path.abspath("iceberg_warehouse")
os.makedirs(WAREHOUSE_PATH, exist_ok=True)
print(f"Warehouse: {WAREHOUSE_PATH}")

# Dùng SQLite làm catalog backend cho đơn giản (local dev)
catalog = SqlCatalog(
    "local",
    **{
        "uri"      : "sqlite:///iceberg_catalog.db",
        "warehouse": f"file://{WAREHOUSE_PATH}",
    }
)

print("Catalog created: iceberg_catalog.db")

if ("movielens",) not in catalog.list_namespaces():
    catalog.create_namespace("movielens")
    print("Namespace 'movielens' created")

schema = Schema(
    NestedField(1, "user_id",   IntegerType(), required=True),
    NestedField(2, "movie_id",  IntegerType(), required=True),
    NestedField(3, "rating",    IntegerType(), required=True),
    NestedField(4, "timestamp", LongType(),    required=True),
)

# Partition theo movie_id bucket để tăng tốc query theo phim
partition_spec = PartitionSpec(
    PartitionField(
        source_id=2,
        field_id=1000,
        transform=BucketTransform(10),
        name="movie_id_bucket"
    )
)

table_name = "movielens.ratings"

if catalog.table_exists(table_name):
    print(f"Table '{table_name}' already exists — skipping")
else:
    catalog.create_table(
        identifier=table_name,
        schema=schema,
        partition_spec=partition_spec,
    )
    print(f"Table '{table_name}' created!")

table = catalog.load_table(table_name)
print(f"\nTable schema:")
print(table.schema())
print(f"\nPartition spec:")
print(table.spec())

print("\nSetup completed!")
