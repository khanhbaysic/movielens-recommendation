import mysql.connector
from datetime import datetime


# =========================
# 1. Connect to MySQL
# =========================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)

cursor = conn.cursor()


# =========================
# 2. Read genre mapping
# =========================

cursor.execute("SELECT genre_id, name FROM genres")

genre_map = {
    name: genre_id
    for genre_id, name in cursor.fetchall()
}

print(f"Loaded {len(genre_map)} genres")


# MovieLens genre columns appear in this exact order
genre_names = [
    "unknown",
    "Action",
    "Adventure",
    "Animation",
    "Children's",
    "Comedy",
    "Crime",
    "Documentary",
    "Drama",
    "Fantasy",
    "Film-Noir",
    "Horror",
    "Musical",
    "Mystery",
    "Romance",
    "Sci-Fi",
    "Thriller",
    "War",
    "Western"
]


# =========================
# 3. Read u.item
# =========================

movies = []
movie_genres = []

with open("ml-100k/u.item", "r", encoding="latin-1") as file:

    for line in file:

        fields = line.rstrip("\n").split("|")

        # First 5 columns
        movie_id = int(fields[0])
        title = fields[1]
        release_date_raw = fields[2]
        imdb_url = fields[4]

        # -------------------------
        # Convert release date
        # -------------------------

        if release_date_raw:
            try:
                release_date = datetime.strptime(
                    release_date_raw,
                    "%d-%b-%Y"
                ).date()
            except ValueError:
                release_date = None
        else:
            release_date = None

        movies.append((
            movie_id,
            title,
            release_date,
            imdb_url
        ))

        # -------------------------
        # Process 19 genre flags
        # -------------------------

        for i, flag in enumerate(fields[5:24]):

            if flag == "1":

                genre_name = genre_names[i]
                genre_id = genre_map[genre_name]

                movie_genres.append((
                    movie_id,
                    genre_id
                ))


print(f"Read {len(movies)} movies")
print(f"Generated {len(movie_genres)} movie-genre relationships")


# =========================
# 4. Insert movies
# =========================

movie_sql = """
INSERT INTO movies
(movie_id, title, release_date, imdb_url)
VALUES (%s, %s, %s, %s)
"""

cursor.executemany(movie_sql, movies)


# =========================
# 5. Insert movie genres
# =========================

genre_sql = """
INSERT INTO movie_genres
(movie_id, genre_id)
VALUES (%s, %s)
"""

cursor.executemany(genre_sql, movie_genres)


# =========================
# 6. Commit
# =========================

conn.commit()

print(f"Inserted {cursor.rowcount} movie-genre relationships")


# =========================
# 7. Close
# =========================

cursor.close()
conn.close()

print("Movie import completed successfully!")