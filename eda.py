import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import warnings
warnings.filterwarnings("ignore")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)

print("=" * 50)
print("   MOVIELENS — EXPLORATORY DATA ANALYSIS")
print("=" * 50)

# Thong ke co ban
queries = {
    "Total users"  : "SELECT COUNT(*) FROM users",
    "Total movies" : "SELECT COUNT(*) FROM movies",
    "Total ratings": "SELECT COUNT(*) FROM ratings",
    "Avg rating"   : "SELECT ROUND(AVG(rating), 4) FROM ratings",
    "Min rating"   : "SELECT MIN(rating) FROM ratings",
    "Max rating"   : "SELECT MAX(rating) FROM ratings",
}

print("\nBasic Statistics:")
print("-" * 35)
for label, sql in queries.items():
    df = pd.read_sql(sql, conn)
    value = df.iloc[0, 0]
    print(f"  {label:<20}: {value}")

df_rating_dist = pd.read_sql("""
    SELECT rating, COUNT(*) AS count
    FROM ratings
    GROUP BY rating
    ORDER BY rating
""", conn)

print("\nRating Distribution:")
print("-" * 35)
print(df_rating_dist.to_string(index=False))

df_top_movies = pd.read_sql("""
    SELECT m.title,
           COUNT(r.rating) AS num_ratings,
           ROUND(AVG(r.rating), 2) AS avg_rating
    FROM ratings r
    JOIN movies m ON r.movie_id = m.movie_id
    GROUP BY m.movie_id, m.title
    ORDER BY num_ratings DESC
    LIMIT 10
""", conn)

print("\nTop 10 Most-Rated Movies:")
print("-" * 60)
print(df_top_movies.to_string(index=False))

df_top_users = pd.read_sql("""
    SELECT r.user_id,
           COUNT(*) AS num_ratings,
           ROUND(AVG(r.rating), 2) AS avg_rating
    FROM ratings r
    GROUP BY r.user_id
    ORDER BY num_ratings DESC
    LIMIT 10
""", conn)

print("\nTop 10 Most Active Users:")
print("-" * 40)
print(df_top_users.to_string(index=False))

df_genre = pd.read_sql("""
    SELECT g.name AS genre,
           COUNT(r.rating) AS num_ratings,
           ROUND(AVG(r.rating), 2) AS avg_rating
    FROM ratings r
    JOIN movie_genres mg ON r.movie_id = mg.movie_id
    JOIN genres g        ON mg.genre_id = g.genre_id
    GROUP BY g.name
    ORDER BY num_ratings DESC
""", conn)

print("\nRatings by Genre:")
print("-" * 45)
print(df_genre.to_string(index=False))

# Sparsity: phan tram o trong trong ma tran user x movie
total_users   = pd.read_sql("SELECT COUNT(*) FROM users",   conn).iloc[0, 0]
total_movies  = pd.read_sql("SELECT COUNT(*) FROM movies",  conn).iloc[0, 0]
total_ratings = pd.read_sql("SELECT COUNT(*) FROM ratings", conn).iloc[0, 0]

sparsity = 1 - (total_ratings / (total_users * total_movies))
print(f"\nMatrix Sparsity: {sparsity:.4%}")
print(f"   ({total_ratings:,} ratings / {total_users * total_movies:,} possible)")

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("MovieLens — EDA", fontsize=16, fontweight="bold")

ax1 = axes[0, 0]
ax1.bar(df_rating_dist["rating"], df_rating_dist["count"],
        color="#4C72B0", edgecolor="white", width=0.6)
ax1.set_title("Rating Distribution")
ax1.set_xlabel("Rating")
ax1.set_ylabel("Count")
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

ax2 = axes[0, 1]
ax2.barh(df_top_movies["title"][::-1], df_top_movies["num_ratings"][::-1],
         color="#DD8452")
ax2.set_title("Top 10 Most-Rated Movies")
ax2.set_xlabel("Number of Ratings")
ax2.tick_params(axis="y", labelsize=8)

ax3 = axes[1, 0]
ax3.barh(df_genre["genre"][::-1], df_genre["num_ratings"][::-1],
         color="#55A868")
ax3.set_title("Number of Ratings by Genre")
ax3.set_xlabel("Number of Ratings")
ax3.tick_params(axis="y", labelsize=8)

ax4 = axes[1, 1]
colors = ["#c44e52" if v < 3.5 else "#4C72B0" for v in df_genre["avg_rating"]]
ax4.barh(df_genre["genre"][::-1], df_genre["avg_rating"][::-1], color=colors[::-1])
ax4.set_title("Avg Rating by Genre")
ax4.set_xlabel("Average Rating")
ax4.set_xlim(0, 5)
ax4.axvline(x=3.5, color="gray", linestyle="--", linewidth=0.8)
ax4.tick_params(axis="y", labelsize=8)

plt.tight_layout()
plt.savefig("eda_plots.png", dpi=150, bbox_inches="tight")
plt.show()
print("\nSaved plot to eda_plots.png")

conn.close()
print("\nEDA completed!")
