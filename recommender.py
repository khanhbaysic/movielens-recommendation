import mysql.connector
import pandas as pd
from surprise import SVD, Dataset, Reader, accuracy
from surprise.model_selection import train_test_split, cross_validate
import pickle
import os

# =========================
# 1. Load ratings từ MySQL
# =========================

print("Connecting to MySQL...")

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)

df = pd.read_sql("""
    SELECT user_id, movie_id, rating
    FROM ratings
""", conn)

print(f"Loaded {len(df):,} ratings from MySQL")
print(f"Users: {df['user_id'].nunique():,}  |  Movies: {df['movie_id'].nunique():,}")


# =========================
# 2. Load movie titles
# =========================

df_movies = pd.read_sql("""
    SELECT movie_id, title
    FROM movies
""", conn)

movie_title = dict(zip(df_movies["movie_id"], df_movies["title"]))

conn.close()


# =========================
# 3. Build Surprise dataset
# =========================

reader = Reader(rating_scale=(1, 5))
data   = Dataset.load_from_df(df[["user_id", "movie_id", "rating"]], reader)


# =========================
# 4. Cross-validate (đánh giá model)
# =========================

print("\nCross-validating SVD (5-fold)...")

svd = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42)

cv_results = cross_validate(svd, data, measures=["RMSE", "MAE"], cv=5, verbose=False)

print(f"  RMSE : {cv_results['test_rmse'].mean():.4f} ± {cv_results['test_rmse'].std():.4f}")
print(f"  MAE  : {cv_results['test_mae'].mean():.4f}  ± {cv_results['test_mae'].std():.4f}")


# =========================
# 5. Train trên toàn bộ data
# =========================

print("\nTraining SVD on full dataset...")

trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
svd.fit(trainset)

predictions = svd.test(testset)
rmse = accuracy.rmse(predictions, verbose=False)
mae  = accuracy.mae(predictions,  verbose=False)

print(f"  Test RMSE: {rmse:.4f}")
print(f"  Test MAE : {mae:.4f}")


# =========================
# 6. Train trên full data & save model
# =========================

full_trainset = data.build_full_trainset()
svd.fit(full_trainset)

with open("svd_model.pkl", "wb") as f:
    pickle.dump(svd, f)

print("\nModel saved to svd_model.pkl")


# =========================
# 7. Hàm recommend
# =========================

def get_recommendations(user_id: int, top_n: int = 10) -> pd.DataFrame:
    """
    Trả về top N phim được dự đoán cao nhất cho user_id,
    loại trừ các phim user đã xem.
    """

    # Phim user đã xem
    seen_movies = set(df[df["user_id"] == user_id]["movie_id"])

    # Tất cả phim chưa xem
    all_movies    = set(df_movies["movie_id"])
    unseen_movies = all_movies - seen_movies

    # Dự đoán rating cho từng phim chưa xem
    predictions_list = [
        (mid, svd.predict(user_id, mid).est)
        for mid in unseen_movies
    ]

    # Sắp xếp theo predicted rating giảm dần
    predictions_list.sort(key=lambda x: x[1], reverse=True)
    top = predictions_list[:top_n]

    result = pd.DataFrame(top, columns=["movie_id", "predicted_rating"])
    result["title"]            = result["movie_id"].map(movie_title)
    result["predicted_rating"] = result["predicted_rating"].round(2)

    return result[["movie_id", "title", "predicted_rating"]].reset_index(drop=True)


# =========================
# 8. Demo recommend
# =========================

print("\n" + "=" * 55)
print("DEMO RECOMMENDATIONS")
print("=" * 55)

for uid in [1, 50, 200]:
    recs = get_recommendations(uid, top_n=5)
    seen_count = len(df[df["user_id"] == uid])
    print(f"\n🎬 Top 5 for User {uid} (đã xem {seen_count} phim):")
    print(recs.to_string(index=False))

print("\nDone!")