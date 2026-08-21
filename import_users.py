import mysql.connector

# 1. Kết nối MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)

cursor = conn.cursor()

# 2. Đọc occupation từ database
cursor.execute("SELECT occupation_id, name FROM occupations")

occupation_map = {
    name: occupation_id
    for occupation_id, name in cursor.fetchall()
}

print(f"Loaded {len(occupation_map)} occupations")

# 3. Đọc u.user
users = []

with open("ml-100k/u.user", "r", encoding="latin-1") as file:
    for line in file:
        user_id, age, gender, occupation, zip_code = line.strip().split("|")

        occupation_id = occupation_map[occupation]

        users.append((
            int(user_id),
            int(age),
            gender,
            occupation_id,
            zip_code
        ))

print(f"Read {len(users)} users")

# 4. Insert vào MySQL
sql = """
INSERT INTO users
(user_id, age, gender, occupation_id, zip_code)
VALUES (%s, %s, %s, %s, %s)
"""

cursor.executemany(sql, users)

conn.commit()

print(f"Inserted {cursor.rowcount} users")

cursor.close()
conn.close()