import mysql.connector

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)
cursor = conn.cursor()

# Load genre map từ DB
cursor.execute("SELECT genre_id, name FROM genres")
genre_map = {name: gid for gid, name in cursor.fetchall()}

movies       = []
movie_genres = []

with open("ml-1m/movies.dat", "r", encoding="latin-1") as f:
    for line in f:
        # Format: MovieID::Title::Genres
        fields   = line.strip().split("::")
        movie_id = int(fields[0])
        title    = fields[1]
        genres   = fields[2].split("|")   # vd: "Action|Comedy"

        # Không có release_date và imdb_url trong 1M
        movies.append((movie_id, title, None, None))

        for genre_name in genres:
            if genre_name in genre_map:
                movie_genres.append((movie_id, genre_map[genre_name]))

print(f"Read {len(movies)} movies")
print(f"Generated {len(movie_genres)} movie-genre relationships")

# Insert movies
cursor.executemany("""
    INSERT INTO movies (movie_id, title, release_date, imdb_url)
    VALUES (%s, %s, %s, %s)
""", movies)

# Insert movie_genres
cursor.executemany("""
    INSERT INTO movie_genres (movie_id, genre_id)
    VALUES (%s, %s)
""", movie_genres)

conn.commit()
print("Movies + genres inserted!")
cursor.close()
conn.close()