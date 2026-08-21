# 🎬 MovieLens Recommendation System

A movie recommendation system built with **SVD (Matrix Factorization)** on the MovieLens 1M dataset, backed by **MySQL** and served via **FastAPI**.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python)
![MySQL](https://img.shields.io/badge/MySQL-8.0-orange?logo=mysql)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green?logo=fastapi)
![SVD](https://img.shields.io/badge/Algorithm-SVD-purple)

---

## 📊 Dataset

[MovieLens 1M](https://grouplens.org/datasets/movielens/1m/) — GroupLens Research

| | Count |
|--|--|
| Users | 6,040 |
| Movies | 3,706 |
| Ratings | 1,000,209 |
| Rating scale | 1 – 5 stars |

---

## 🏗️ Architecture

```
MySQL (Database)
  ├── users · movies · ratings
  ├── genres · movie_genres · occupations
        ↓
Python + SVD (scikit-surprise)
  └── Train model → svd_model.pkl  (RMSE: 0.8731)
        ↓
FastAPI (REST API)
  └── /recommend · /movies · /users · /top-movies
        ↓
HTML + CSS + JS (Frontend)
  └── Gợi ý phim · Lịch sử · Top phim
```

---

## 📁 Project Structure

```
movielens/
│
├── movielen_schema.sql       # MySQL schema + seed data
│
├── import_users.py           # Import users (100K)
├── import_movies.py          # Import movies + genres (100K)
├── import_ratings.py         # Import ratings (100K)
│
├── import_users_1m.py        # Import users (1M)
├── import_movies_1m.py       # Import movies + genres (1M)
├── import_ratings_1m.py      # Import ratings (1M)
│
├── eda.py                    # Exploratory Data Analysis
├── recommender.py            # Train SVD model
├── api.py                    # FastAPI REST API
├── index.html                # Frontend UI
│
└── ml-1m/                    # Dataset (not included, download separately)
```

---

## ⚙️ Setup

### 1. Clone repo
```bash
git clone https://github.com/YOUR_USERNAME/movielens-recommendation.git
cd movielens-recommendation
```

### 2. Install dependencies
```bash
pip install mysql-connector-python pandas matplotlib scikit-surprise fastapi uvicorn
```

### 3. Download dataset
Download [MovieLens 1M](https://grouplens.org/datasets/movielens/1m/), extract and place the `ml-1m/` folder in the project directory.

### 4. Setup MySQL
- Create database `movielens`
- Run `movielen_schema.sql` in MySQL Workbench
- Update your MySQL password in each script

### 5. Import data
```bash
python import_users_1m.py
python import_movies_1m.py
python import_ratings_1m.py
```

### 6. Train model
```bash
python recommender.py
```

### 7. Start API
```bash
uvicorn api:app --reload
```

### 8. Open frontend
Open `index.html` in your browser.

---

## 🚀 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/recommend/{user_id}?top_n=10` | Top N movie recommendations |
| GET | `/movies/{movie_id}` | Movie detail |
| GET | `/users/{user_id}/history` | User rating history |
| GET | `/top-movies?limit=10` | Top rated movies |
| GET | `/docs` | Swagger UI |

**Example:**
```bash
curl http://localhost:8000/recommend/1?top_n=5
```

---

## 📈 Model Performance

| Metric | Score |
|--------|-------|
| RMSE | **0.8731** |
| Algorithm | SVD (n_factors=100, n_epochs=20) |
| Dataset | MovieLens 1M |

---

## 🗄️ Database Schema

```
occupations ──┐
              ├── users ──┐
genres ───────┤           ├── ratings
              └── movies ─┤
movie_genres ─────────────┘
```

---

## 🔮 Roadmap (Phase 2)

- [ ] Kafka — Real-time rating ingestion
- [ ] Flink — Stream processing & aggregation
- [ ] Apache Iceberg — Data lake storage
- [ ] Agentic AI — Intelligent recommendation agent

---

## 📚 References

- [MovieLens Datasets — GroupLens](https://grouplens.org/datasets/movielens/)
- [scikit-surprise Documentation](https://surprise.readthedocs.io/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
