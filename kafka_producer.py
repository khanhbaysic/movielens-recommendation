import json
import time
import random
import mysql.connector
from kafka import KafkaProducer
from datetime import datetime

# Lấy danh sách user và movie từ DB để random
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)
cursor = conn.cursor()

cursor.execute("SELECT user_id FROM users")
user_ids = [row[0] for row in cursor.fetchall()]

cursor.execute("SELECT movie_id FROM movies")
movie_ids = [row[0] for row in cursor.fetchall()]

cursor.close()
conn.close()

print(f"Loaded {len(user_ids)} users | {len(movie_ids)} movies")

producer = KafkaProducer(
    bootstrap_servers="localhost:9092",
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

print("Producer connected to Kafka!")
print("Simulating real-time ratings... (Ctrl+C to stop)\n")

count = 0

try:
    while True:
        # Tạo rating ngẫu nhiên và đẩy lên Kafka
        event = {
            "user_id"  : random.choice(user_ids),
            "movie_id" : random.choice(movie_ids),
            "rating"   : random.randint(1, 5),
            "timestamp": int(time.time())
        }

        producer.send("movielens-ratings", value=event)
        count += 1

        print(f"[{datetime.now().strftime('%H:%M:%S')}] "
              f"Sent #{count:>5} | "
              f"user={event['user_id']:<5} "
              f"movie={event['movie_id']:<5} "
              f"rating={event['rating']}⭐")

        time.sleep(0.5)

except KeyboardInterrupt:
    print(f"\nStopped. Total sent: {count} events")
    producer.close()
