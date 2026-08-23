import os
from dotenv import load_dotenv
import mysql.connector

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "movielens")
)
cursor = conn.cursor()

ratings = []

with open("ml-1m/ratings.dat", "r", encoding="latin-1") as f:
    for line in f:
        # Format: UserID::MovieID::Rating::Timestamp
        fields    = line.strip().split("::")
        user_id   = int(fields[0])
        movie_id  = int(fields[1])
        rating    = int(fields[2])
        timestamp = int(fields[3])

        ratings.append((user_id, movie_id, rating, timestamp))

print(f"Read {len(ratings):,} ratings")

sql = """
INSERT INTO ratings (user_id, movie_id, rating, timestamp)
VALUES (%s, %s, %s, %s)
"""

BATCH_SIZE = 10000
for i in range(0, len(ratings), BATCH_SIZE):
    batch = ratings[i : i + BATCH_SIZE]
    cursor.executemany(sql, batch)
    conn.commit()
    print(f"  Inserted {i + len(batch):,} / {len(ratings):,}")

cursor.execute("SELECT COUNT(*) FROM ratings")
print(f"\nTotal in DB: {cursor.fetchone()[0]:,}")

cursor.close()
conn.close()
print("Done!")