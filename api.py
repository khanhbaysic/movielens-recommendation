import mysql.connector
import pandas as pd
import pickle
from fastapi import FastAPI, HTTPException
from surprise import SVD

# =========================
# 1. Load model & data
# =========================

print("Loading model...")
with open("svd_model.pkl", "rb") as f:
    svd: SVD = pickle.load(f)

print("Connecting to MySQL...")
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)

df_ratings = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", conn)

df_movies = pd.read_sql("""
    SELECT m.movie_id, m.title, m.release_date,
           GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
    FROM movies m
    LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
    LEFT JOIN genres g        ON mg.genre_id = g.genre_id
    GROUP BY m.movie_id, m.title, m.release_date
""", conn)

conn.close()

movie_info  = df_movies.set_index("movie_id").to_dict("index")
all_movie_ids = set(df_movies["movie_id"])

print(f"Ready! {len(df_ratings):,} ratings | {len(df_movies):,} movies")


# =========================
# 2. App
# =========================

app = FastAPI(
    title="MovieLens Recommendation API",
    description="SVD-based movie recommendation system",
    version="1.0.0"
)
from fastapi.middleware.cors import CORSMiddleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================
# 3. Routes
# =========================

@app.get("/")
def root():
    return {
        "message": "MovieLens Recommendation API",
        "endpoints": {
            "recommend"   : "/recommend/{user_id}?top_n=10",
            "movie info"  : "/movies/{movie_id}",
            "user history": "/users/{user_id}/history?limit=10",
            "top movies"  : "/movies/top?limit=10",
        }
    }


@app.get("/recommend/{user_id}")
def recommend(user_id: int, top_n: int = 10):
    """Trả về top N phim được dự đoán cho user."""

    # Kiểm tra user tồn tại
    seen = df_ratings[df_ratings["user_id"] == user_id]["movie_id"]
    if seen.empty:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    seen_set    = set(seen)
    unseen_ids  = all_movie_ids - seen_set

    # Dự đoán
    preds = [
        (mid, round(svd.predict(user_id, mid).est, 2))
        for mid in unseen_ids
    ]
    preds.sort(key=lambda x: x[1], reverse=True)
    top = preds[:top_n]

    results = []
    for mid, score in top:
        info = movie_info.get(mid, {})
        results.append({
            "movie_id"        : mid,
            "title"           : info.get("title", "Unknown"),
            "genres"          : info.get("genres", ""),
            "release_date"    : str(info.get("release_date", "")),
            "predicted_rating": score
        })

    return {
        "user_id"      : user_id,
        "seen_movies"  : len(seen_set),
        "top_n"        : top_n,
        "recommendations": results
    }


@app.get("/movies/{movie_id}")
def get_movie(movie_id: int):
    """Thông tin chi tiết một bộ phim."""
    if movie_id not in movie_info:
        raise HTTPException(status_code=404, detail=f"Movie {movie_id} not found")

    info = movie_info[movie_id]
    stats = df_ratings[df_ratings["movie_id"] == movie_id]["rating"]

    return {
        "movie_id"   : movie_id,
        "title"      : info["title"],
        "genres"     : info["genres"],
        "release_date": str(info["release_date"]),
        "num_ratings": int(len(stats)),
        "avg_rating" : round(float(stats.mean()), 2) if len(stats) > 0 else None
    }


@app.get("/users/{user_id}/history")
def user_history(user_id: int, limit: int = 10):
    """Lịch sử rating của user."""
    user_df = df_ratings[df_ratings["user_id"] == user_id]
    if user_df.empty:
        raise HTTPException(status_code=404, detail=f"User {user_id} not found")

    top = user_df.sort_values("rating", ascending=False).head(limit)

    history = []
    for _, row in top.iterrows():
        info = movie_info.get(row["movie_id"], {})
        history.append({
            "movie_id": int(row["movie_id"]),
            "title"   : info.get("title", "Unknown"),
            "rating"  : int(row["rating"])
        })

    return {
        "user_id"      : user_id,
        "total_ratings": len(user_df),
        "history"      : history
    }


@app.get("/top-movies")
def top_movies(limit: int = 10):
    """Top phim được đánh giá cao nhất (tối thiểu 50 ratings)."""
    stats = df_ratings.groupby("movie_id").agg(
        num_ratings=("rating", "count"),
        avg_rating =("rating", "mean")
    ).reset_index()

    stats = stats[stats["num_ratings"] >= 50]
    stats = stats.sort_values("avg_rating", ascending=False).head(limit)

    results = []
    for _, row in stats.iterrows():
        info = movie_info.get(row["movie_id"], {})
        results.append({
            "movie_id"   : int(row["movie_id"]),
            "title"      : info.get("title", "Unknown"),
            "genres"     : info.get("genres", ""),
            "num_ratings": int(row["num_ratings"]),
            "avg_rating" : round(row["avg_rating"], 2)
        })

    return {"top_movies": results}