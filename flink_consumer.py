import json
import time
import mysql.connector
from kafka import KafkaConsumer
from collections import defaultdict
from datetime import datetime

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)
cursor = conn.cursor()

# Lấy set user và movie hợp lệ để validate message từ Kafka
cursor.execute("SELECT user_id FROM users")
valid_users = set(row[0] for row in cursor.fetchall())

cursor.execute("SELECT movie_id FROM movies")
valid_movies = set(row[0] for row in cursor.fetchall())

print(f"Loaded {len(valid_users)} valid users | {len(valid_movies)} valid movies")

consumer = KafkaConsumer(
    "movielens-ratings",
    bootstrap_servers="localhost:9092",
    value_deserializer=lambda v: json.loads(v.decode("utf-8")),
    auto_offset_reset="latest",
    group_id="flink-consumer-group"
)

print("Consumer connected to Kafka!")
print("Listening for real-time ratings...\n")
print(f"{'Time':<12} {'Status':<10} {'User':<8} {'Movie':<8} {'Rating':<8} {'Note'}")
print("-" * 65)

# Lưu ratings trong 30s gần nhất để tính moving average
window = defaultdict(list)
WINDOW_SECONDS = 30

total_received = 0
total_inserted = 0
total_invalid  = 0
last_report    = time.time()


def validate(event):
    uid = event.get("user_id")
    mid = event.get("movie_id")
    r   = event.get("rating")

    if uid not in valid_users:
        return False, "Invalid user"
    if mid not in valid_movies:
        return False, "Invalid movie"
    if not isinstance(r, int) or not (1 <= r <= 5):
        return False, f"Invalid rating: {r}"
    return True, "OK"


def insert_rating(event):
    # Dùng ON DUPLICATE KEY UPDATE vì user có thể rate lại cùng 1 phim
    sql = """
        INSERT INTO ratings (user_id, movie_id, rating, timestamp)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            rating    = VALUES(rating),
            timestamp = VALUES(timestamp)
    """
    cursor.execute(sql, (
        event["user_id"],
        event["movie_id"],
        event["rating"],
        event["timestamp"]
    ))
    conn.commit()


def print_window_stats():
    now = time.time()

    # Chỉ giữ lại events trong window 30 giây
    active = {
        mid: [r for ts, r in ratings if now - ts <= WINDOW_SECONDS]
        for mid, ratings in window.items()
    }
    active = {mid: rs for mid, rs in active.items() if rs}

    if not active:
        return

    stats = sorted(
        [(mid, sum(rs)/len(rs), len(rs)) for mid, rs in active.items()],
        key=lambda x: x[1], reverse=True
    )[:5]

    print(f"\n{'='*65}")
    print(f"📊 [{datetime.now().strftime('%H:%M:%S')}] "
          f"Window Stats (last {WINDOW_SECONDS}s) | "
          f"Received: {total_received} | "
          f"Inserted: {total_inserted} | "
          f"Invalid: {total_invalid}")
    print(f"  {'Movie ID':<12} {'Avg Rating':<14} {'Count'}")
    print(f"  {'-'*35}")
    for mid, avg, cnt in stats:
        bar = "⭐" * round(avg)
        print(f"  {mid:<12} {avg:<8.2f} {bar:<14} ({cnt} ratings)")
    print(f"{'='*65}\n")


try:
    for message in consumer:
        event = message.value
        total_received += 1

        is_valid, note = validate(event)
        status = "✅ OK" if is_valid else "❌ SKIP"

        ts  = datetime.now().strftime("%H:%M:%S")
        uid = event.get("user_id", "?")
        mid = event.get("movie_id", "?")
        r   = event.get("rating", "?")

        print(f"{ts:<12} {status:<10} {str(uid):<8} {str(mid):<8} {str(r):<8} {note}")

        if is_valid:
            insert_rating(event)
            total_inserted += 1
            window[mid].append((time.time(), r))

        # In thống kê mỗi 30 giây
        if time.time() - last_report >= WINDOW_SECONDS:
            print_window_stats()
            last_report = time.time()

except KeyboardInterrupt:
    print(f"\nStopped.")
    print(f"Total received : {total_received}")
    print(f"Total inserted : {total_inserted}")
    print(f"Total invalid  : {total_invalid}")

finally:
    cursor.close()
    conn.close()
    consumer.close()
    print("Connections closed.")
