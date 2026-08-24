import os
import sys
import json
import time
import mysql.connector
import pandas as pd
import pickle
from dotenv import load_dotenv
from google import genai
from collections import defaultdict

sys.stdout.reconfigure(encoding="utf-8")
sys.stdin.reconfigure(encoding="utf-8")

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL  = "gemini-3.6-flash"

print("Loading SVD model...")
with open("svd_model.pkl", "rb") as f:
    svd = pickle.load(f)

print("Loading data from MySQL...")
conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME", "movielens")
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


# ── TOOLS ─────────────────────────────────────────────────────────────────────

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


def get_genre_preference(user_id: int) -> str:
    """Phan tich genre user thich nhat dua tren lich su rating."""
    user_df = df_ratings[df_ratings["user_id"] == user_id]
    if user_df.empty:
        return f"Không tìm thấy user {user_id}."

    genre_stats = defaultdict(lambda: {"count": 0, "total": 0})

    for _, row in user_df.iterrows():
        info   = movie_info.get(row["movie_id"], {})
        genres = info.get("genres", "")
        for genre in genres.split(", "):
            genre = genre.strip()
            if genre:
                genre_stats[genre]["count"] += 1
                genre_stats[genre]["total"] += row["rating"]

    genre_avg = [
        (g, d["total"] / d["count"], d["count"])
        for g, d in genre_stats.items()
        if d["count"] >= 3
    ]
    genre_avg.sort(key=lambda x: x[1], reverse=True)

    lines = [f"Genre preference của user {user_id} (dựa trên {len(user_df)} ratings):"]
    for genre, avg, count in genre_avg[:8]:
        lines.append(f"  - {genre:<15} avg {avg:.2f}/5  ({count} phim)")
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
    "get_user_history"    : lambda p: get_user_history(p["user_id"], p.get("limit", 10)),
    "get_genre_preference": lambda p: get_genre_preference(p["user_id"]),
    "get_recommendations" : lambda p: get_recommendations(p["user_id"], p.get("genre_filter"), p.get("top_n", 10)),
    "get_top_movies"      : lambda p: get_top_movies(p.get("genre_filter"), p.get("limit", 10)),
    "search_movies"       : lambda p: search_movies(p["keyword"]),
}

TOOLS_DESC = """
Tools có sẵn:
1. get_user_history(user_id, limit=10) — lịch sử phim đã xem
2. get_genre_preference(user_id) — genre user thích nhất
3. get_recommendations(user_id, genre_filter=null, top_n=10) — gợi ý phim SVD
4. get_top_movies(genre_filter=null, limit=10) — top phim cộng đồng
5. search_movies(keyword) — tìm phim theo tên
"""


def gemini_call(prompt: str) -> str:
    for attempt in range(3):
        try:
            return client.models.generate_content(model=MODEL, contents=prompt).text
        except Exception as e:
            if "503" in str(e) and attempt < 2:
                print("  [Gemini bận, thử lại...]")
                time.sleep(3)
            else:
                raise


def plan_and_execute(query: str) -> str:
    # Gemini len ke hoach: chon 1-2 tools phu hop
    plan_prompt = f"""
Bạn là AI tư vấn phim. Người dùng hỏi: "{query}"

{TOOLS_DESC}

Chọn 1-2 tools phù hợp nhất. Nếu user hỏi gợi ý phim cá nhân → gọi get_genre_preference trước, sau đó get_recommendations.

Trả về JSON (chỉ JSON):
{{
  "reasoning": "lý do ngắn gọn",
  "tool_calls": [
    {{"tool": "tên_tool", "params": {{"key": value}}}}
  ]
}}
"""
    text = gemini_call(plan_prompt).strip()
    if "```" in text:
        text = text.split("```")[1].replace("json", "").strip()

    plan      = json.loads(text)
    reasoning = plan.get("reasoning", "")
    print(f"  [Kế hoạch: {reasoning}]")

    # Thuc thi tung tool
    results = []
    for call in plan.get("tool_calls", []):
        tool_name = call.get("tool")
        params    = call.get("params", {})
        if tool_name not in TOOL_MAP:
            continue
        print(f"  [Gọi: {tool_name}({params})]")
        results.append(f"### {tool_name}:\n{TOOL_MAP[tool_name](params)}")

    if not results:
        return "Xin lỗi, không tìm được thông tin phù hợp."

    # Tong hop thanh cau tra loi tu nhien co giai thich
    final_prompt = f"""
Người dùng hỏi: "{query}"

Dữ liệu:
{chr(10).join(results)}

Trả lời tự nhiên, thân thiện bằng tiếng Việt. Giải thích lý do gợi ý dựa trên dữ liệu (ví dụ: "Vì bạn thích Drama..."). Ngắn gọn, không liệt kê quá dài.
"""
    return gemini_call(final_prompt)


# ── MAIN LOOP ─────────────────────────────────────────────────────────────────

print("=" * 60)
print("  MOVIELENS AI AGENT  (nhập 'quit' để thoát)")
print("=" * 60)
print("Ví dụ:")
print("  'Gợi ý phim hay cho user 1'")
print("  'User 42 thích thể loại gì?'")
print("  'Top phim Thriller hay nhất'")
print("  'Tìm phim có tên Star Wars'")
print("=" * 60 + "\n")

while True:
    user_input = input("Bạn: ").strip()

    if user_input.lower() in ("quit", "exit", "thoát"):
        print("Tạm biệt!")
        break
    if not user_input:
        continue

    try:
        answer = plan_and_execute(user_input)
        print(f"\nAgent: {answer}\n")
    except Exception as e:
        print(f"\nAgent: Xin lỗi, có lỗi xảy ra: {e}\n")