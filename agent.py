import os
import sys
import json
import mysql.connector
import pandas as pd
import pickle
from dotenv import load_dotenv
from google import genai

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL  = "gemini-3.6-flash"

# Load SVD model
print("Loading SVD model...")
with open("svd_model.pkl", "rb") as f:
    svd = pickle.load(f)

# Load data từ MySQL
print("Loading data from MySQL...")
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Quockhanh1234",
    database="movielens"
)

df_ratings = pd.read_sql("SELECT user_id, movie_id, rating FROM ratings", conn)

df_movies = pd.read_sql("""
    SELECT m.movie_id, m.title,
           GROUP_CONCAT(g.name ORDER BY g.name SEPARATOR ', ') AS genres
    FROM movies m
    LEFT JOIN movie_genres mg ON m.movie_id = mg.movie_id
    LEFT JOIN genres g        ON mg.genre_id = g.genre_id
    GROUP BY m.movie_id, m.title
""", conn)

conn.close()

movie_info    = df_movies.set_index("movie_id").to_dict("index")
all_movie_ids = set(df_movies["movie_id"])

print(f"Ready! {len(df_ratings):,} ratings | {len(df_movies):,} movies\n")


# Tools
def get_user_history(user_id: int, limit: int = 10) -> str:
    user_df = df_ratings[df_ratings["user_id"] == user_id]
    if user_df.empty:
        return f"Không tìm thấy user {user_id}."

    top   = user_df.sort_values("rating", ascending=False).head(limit)
    lines = [f"User {user_id} đã xem {len(user_df)} phim. Top {limit} phim yêu thích:"]
    for _, row in top.iterrows():
        info = movie_info.get(row["movie_id"], {})
        lines.append(f"  - {info.get('title','?')} | {info.get('genres','?')} | {int(row['rating'])}/5 sao")
    return "\n".join(lines)


def get_recommendations(user_id: int, genre_filter: str = None, top_n: int = 10) -> str:
    seen   = set(df_ratings[df_ratings["user_id"] == user_id]["movie_id"])
    unseen = all_movie_ids - seen

    preds = [(mid, svd.predict(user_id, mid).est) for mid in unseen]
    preds.sort(key=lambda x: x[1], reverse=True)

    results = []
    for mid, score in preds:
        info   = movie_info.get(mid, {})
        genres = info.get("genres", "")
        if genre_filter and genre_filter.lower() not in genres.lower():
            continue
        results.append(f"  - {info.get('title','?')} | {genres} | dự đoán {score:.2f}/5")
        if len(results) >= top_n:
            break

    if not results:
        return f"Không tìm thấy phim phù hợp với genre '{genre_filter}'."

    header = f"Top {len(results)} phim gợi ý cho user {user_id}"
    if genre_filter:
        header += f" (genre: {genre_filter})"
    return header + ":\n" + "\n".join(results)


def get_top_movies(genre_filter: str = None, limit: int = 10) -> str:
    stats = df_ratings.groupby("movie_id").agg(
        num_ratings=("rating", "count"),
        avg_rating =("rating", "mean")
    ).reset_index()

    stats = stats[stats["num_ratings"] >= 50].sort_values("avg_rating", ascending=False)

    lines = []
    for _, row in stats.iterrows():
        info   = movie_info.get(row["movie_id"], {})
        genres = info.get("genres", "")
        if genre_filter and genre_filter.lower() not in genres.lower():
            continue
        lines.append(f"  - {info.get('title','?')} | {genres} | {row['avg_rating']:.2f}/5 ({int(row['num_ratings'])} votes)")
        if len(lines) >= limit:
            break

    header = "Top phim được đánh giá cao nhất"
    if genre_filter:
        header += f" (genre: {genre_filter})"
    return header + ":\n" + "\n".join(lines)


def search_movies(keyword: str) -> str:
    matches = df_movies[df_movies["title"].str.contains(keyword, case=False, na=False)]
    if matches.empty:
        return f"Không tìm thấy phim nào có từ khóa '{keyword}'."

    lines = [f"Tìm thấy {len(matches)} phim:"]
    for _, row in matches.head(10).iterrows():
        lines.append(f"  - [{row['movie_id']}] {row['title']} | {row['genres']}")
    return "\n".join(lines)


TOOL_MAP = {
    "recommend" : lambda p: get_recommendations(p["user_id"], p.get("genre"), p.get("top_n", 10)),
    "history"   : lambda p: get_user_history(p["user_id"], p.get("limit", 10)),
    "top_movies": lambda p: get_top_movies(p.get("genre"), p.get("limit", 10)),
    "search"    : lambda p: search_movies(p["keyword"]),
}


def parse_intent(query: str) -> dict:
    """Dùng Gemini để hiểu ý định người dùng và trả về JSON."""
    prompt = f"""
Phân tích câu hỏi sau và trả về JSON:

Câu hỏi: "{query}"

Trả về JSON theo đúng format này:
{{
    "action": "recommend" hoặc "history" hoặc "top_movies" hoặc "search",
    "user_id": <số nguyên hoặc null>,
    "genre": "<tên genre bằng tiếng Anh hoặc null>",
    "keyword": "<từ khóa tìm kiếm hoặc null>",
    "top_n": <số nguyên, mặc định 10>,
    "limit": <số nguyên, mặc định 10>
}}

Chỉ trả về JSON, không giải thích thêm.
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    text = response.text.strip()

    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    return json.loads(text)


def format_response(query: str, data: str) -> str:
    """Dùng Gemini để format kết quả thành câu trả lời tự nhiên."""
    prompt = f"""
Người dùng hỏi: "{query}"

Dữ liệu từ hệ thống:
{data}

Hãy trả lời người dùng một cách tự nhiên, ngắn gọn, thân thiện bằng tiếng Việt.
"""
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text


# Agent loop
print("=" * 55)
print("  MOVIELENS AI AGENT  (nhập 'quit' để thoát)")
print("=" * 55)
print("Ví dụ:")
print("  'Gợi ý phim cho user 1'")
print("  'Top phim Action hay nhất'")
print("  'User 50 thích phim gì'")
print("  'Tìm phim có tên Star Wars'")
print("=" * 55 + "\n")

while True:
    user_input = input("Bạn: ").strip()

    if user_input.lower() in ("quit", "exit", "thoát"):
        print("Tạm biệt!")
        break
    if not user_input:
        continue

    try:
        # Bước 1: Hiểu ý định
        intent = parse_intent(user_input)
        print(f"  [Agent: {intent}]")

        # Bước 2: Gọi tool phù hợp
        action = intent.get("action", "top_movies")
        data   = TOOL_MAP[action](intent)

        # Bước 3: Format câu trả lời tự nhiên
        answer = format_response(user_input, data)
        print(f"\nAgent: {answer}\n")

    except Exception as e:
        print(f"\nAgent: Xin lỗi, có lỗi xảy ra: {e}\n")