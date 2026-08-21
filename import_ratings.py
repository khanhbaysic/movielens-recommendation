import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)
cursor = conn.cursor()

# u.data dung tab de phan cach cac cot
ratings = []

with open("ml-100k/u.data", "r", encoding="latin-1") as file:
    for line in file:
        fields = line.strip().split("\t")

        user_id   = int(fields[0])
        movie_id  = int(fields[1])
        rating    = int(fields[2])
        timestamp = int(fields[3])

        ratings.append((user_id, movie_id, rating, timestamp))

print(f"Read {len(ratings)} ratings")

sql = """
INSERT INTO ratings (user_id, movie_id, rating, timestamp)
VALUES (%s, %s, %s, %s)
"""

# Insert theo batch de tranh timeout
BATCH_SIZE = 5000

for i in range(0, len(ratings), BATCH_SIZE):
    batch = ratings[i : i + BATCH_SIZE]
    cursor.executemany(sql, batch)
    conn.commit()
    print(f"  Inserted rows {i+1} to {i+len(batch)}")

cursor.execute("SELECT COUNT(*) FROM ratings")
count = cursor.fetchone()[0]
print(f"\nTotal ratings in DB: {count}")

cursor.execute("""
    SELECT u.user_id, m.title, r.rating
    FROM ratings r
    JOIN users u  ON r.user_id  = u.user_id
    JOIN movies m ON r.movie_id = m.movie_id
    LIMIT 5
""")

print("\nSample ratings:")
print(f"{'user_id':<10} {'title':<40} {'rating':<6}")
print("-" * 56)
for row in cursor.fetchall():
    print(f"{row[0]:<10} {row[1]:<40} {row[2]:<6}")

cursor.close()
conn.close()
print("\nRatings import completed successfully!")
