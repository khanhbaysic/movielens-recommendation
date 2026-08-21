import mysql.connector
import pandas as pd
from surprise import SVD, Dataset, Reader, accuracy
from surprise.model_selection import train_test_split, cross_validate
import pickle

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

df_movies = pd.read_sql("""
    SELECT movie_id, title
    FROM movies
""", conn)

movie_title = dict(zip(df_movies["movie_id"], df_movies["title"]))

conn.close()

reader = Reader(rating_scale=(1, 5))
data   = Dataset.load_from_df(df[["user_id", "movie_id", "rating"]], reader)

# Cross-validate de danh gia model truoc khi train full
print("\nCross-validating SVD (5-fold)...")

svd = SVD(n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42)

cv_results = cross_validate(svd, data, measures=["RMSE", "MAE"], cv=5, verbose=False)

print(f"  RMSE : {cv_results['test_rmse'].mean():.4f} +/- {cv_results['test_rmse'].std():.4f}")
print(f"  MAE  : {cv_results['test_mae'].mean():.4f}  +/- {cv_results['test_mae'].std():.4f}")

print("\nTraining SVD on full dataset...")

trainset, testset = train_test_split(data, test_size=0.2, random_state=42)
svd.fit(trainset)

predictions = svd.test(testset)
rmse = accuracy.rmse(predictions, verbose=False)
mae  = accuracy.mae(predictions,  verbose=False)

print(f"  Test RMSE: {rmse:.4f}")
print(f"  Test MAE : {mae:.4f}")

# Train lai tren toan bo data roi luu model
full_trainset = data.build_full_trainset()
svd.fit(full_trainset)

with open("svd_model.pkl", "wb") as f:
    pickle.dump(svd, f)

print("\nModel saved to svd_model.pkl")


def get_recommendations(user_id: int, top_n: int = 10) -> pd.DataFrame:
    """Tra ve top N phim chua xem co predicted rating cao nhat cho user."""

    seen_movies   = set(df[df["user_id"] == user_id]["movie_id"])
    all_movies    = set(df_movies["movie_id"])
    unseen_movies = all_movies - seen_movies

    predictions_list = [
        (mid, svd.predict(user_id, mid).est)
        for mid in unseen_movies
    ]

    predictions_list.sort(key=lambda x: x[1], reverse=True)
    top = predictions_list[:top_n]

    result = pd.DataFrame(top, columns=["movie_id", "predicted_rating"])
    result["title"]            = result["movie_id"].map(movie_title)
    result["predicted_rating"] = result["predicted_rating"].round(2)

    return result[["movie_id", "title", "predicted_rating"]].reset_index(drop=True)


print("\n" + "=" * 55)
print("DEMO RECOMMENDATIONS")
print("=" * 55)

for uid in [1, 50, 200]:
    recs = get_recommendations(uid, top_n=5)
    seen_count = len(df[df["user_id"] == uid])
    print(f"\nTop 5 for User {uid} (da xem {seen_count} phim):")
    print(recs.to_string(index=False))

print("\nDone!")
