import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import warnings
warnings.filterwarnings("ignore")

# =========================
# 1. Connect to MySQL
# =========================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)

print("=" * 50)
print("   MOVIELENS 100K — EXPLORATORY DATA ANALYSIS")
print("=" * 50)


# =========================
# 2. Basic stats
# =========================

queries = {
    "Total users"  : "SELECT COUNT(*) FROM users",
    "Total movies" : "SELECT COUNT(*) FROM movies",
    "Total ratings": "SELECT COUNT(*) FROM ratings",
    "Avg rating"   : "SELECT ROUND(AVG(rating), 4) FROM ratings",
    "Min rating"   : "SELECT MIN(rating) FROM ratings",
    "Max rating"   : "SELECT MAX(rating) FROM ratings",
}

print("\n📊 Basic Statistics:")
print("-" * 35)
for label, sql in queries.items():
    df = pd.read_sql(sql, conn)
    value = df.iloc[0, 0]
    print(f"  {label:<20}: {value}")


# =========================
# 3. Rating distribution
# =========================

df_rating_dist = pd.read_sql("""
    SELECT rating, COUNT(*) AS count
    FROM ratings
    GROUP BY rating
    ORDER BY rating
""", conn)

print("\n⭐ Rating Distribution:")
print("-" * 35)
print(df_rating_dist.to_string(index=False))


# =========================
# 4. Top 10 most-rated movies
# =========================

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

print("\n🎬 Top 10 Most-Rated Movies:")
print("-" * 60)
print(df_top_movies.to_string(index=False))


# =========================
# 5. Top 10 most active users
# =========================

df_top_users = pd.read_sql("""
    SELECT r.user_id,
           COUNT(*) AS num_ratings,
           ROUND(AVG(r.rating), 2) AS avg_rating
    FROM ratings r
    GROUP BY r.user_id
    ORDER BY num_ratings DESC
    LIMIT 10
""", conn)

print("\n👤 Top 10 Most Active Users:")
print("-" * 40)
print(df_top_users.to_string(index=False))


# =========================
# 6. Rating count per genre
# =========================

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

print("\n🎭 Ratings by Genre:")
print("-" * 45)
print(df_genre.to_string(index=False))


# =========================
# 7. Sparsity
# =========================

total_users  = pd.read_sql("SELECT COUNT(*) FROM users",   conn).iloc[0, 0]
total_movies = pd.read_sql("SELECT COUNT(*) FROM movies",  conn).iloc[0, 0]
total_ratings= pd.read_sql("SELECT COUNT(*) FROM ratings", conn).iloc[0, 0]

sparsity = 1 - (total_ratings / (total_users * total_movies))
print(f"\n🔍 Matrix Sparsity: {sparsity:.4%}")
print(f"   ({total_ratings:,} ratings / {total_users * total_movies:,} possible)")


# =========================
# 8. Plots
# =========================

fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle("MovieLens 100K — EDA", fontsize=16, fontweight="bold")

# Plot 1: Rating distribution
ax1 = axes[0, 0]
ax1.bar(df_rating_dist["rating"], df_rating_dist["count"],
        color="#4C72B0", edgecolor="white", width=0.6)
ax1.set_title("Rating Distribution")
ax1.set_xlabel("Rating")
ax1.set_ylabel("Count")
ax1.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

# Plot 2: Top 10 most-rated movies (horizontal bar)
ax2 = axes[0, 1]
ax2.barh(df_top_movies["title"][::-1], df_top_movies["num_ratings"][::-1],
         color="#DD8452")
ax2.set_title("Top 10 Most-Rated Movies")
ax2.set_xlabel("Number of Ratings")
ax2.tick_params(axis="y", labelsize=8)

# Plot 3: Ratings by genre
ax3 = axes[1, 0]
ax3.barh(df_genre["genre"][::-1], df_genre["num_ratings"][::-1],
         color="#55A868")
ax3.set_title("Number of Ratings by Genre")
ax3.set_xlabel("Number of Ratings")
ax3.tick_params(axis="y", labelsize=8)

# Plot 4: Avg rating by genre
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
print("\n✅ Saved plot to eda_plots.png")


# =========================
# 9. Close
# =========================

conn.close()
print("\nEDA completed!")