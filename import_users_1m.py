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

# Age group mapping (1M dùng nhóm tuổi, không phải tuổi thật)
# 1=Under 18, 18=18-24, 25=25-34, 35=35-44, 45=45-49, 50=50-55, 56=56+

users = []

with open("ml-1m/users.dat", "r", encoding="latin-1") as f:
    for line in f:
        # Format: UserID::Gender::Age::Occupation::Zip-code
        fields = line.strip().split("::")
        user_id     = int(fields[0])
        gender      = fields[1]
        age         = int(fields[2])       # age group
        occupation  = int(fields[3])
        zip_code    = fields[4]

        users.append((user_id, age, gender, occupation, zip_code))

print(f"Read {len(users)} users")

sql = """
INSERT INTO users (user_id, age, gender, occupation_id, zip_code)
VALUES (%s, %s, %s, %s, %s)
"""
cursor.executemany(sql, users)
conn.commit()

print(f"Inserted {cursor.rowcount} users")
cursor.close()
conn.close()
print("Done!")