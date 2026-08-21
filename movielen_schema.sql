USE movielens;

CREATE TABLE occupations (
    occupation_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE genres (
    genre_id INT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE users (
    user_id INT PRIMARY KEY,
    age INT NOT NULL,
    gender CHAR(1) NOT NULL,
    occupation_id INT NOT NULL,
    zip_code VARCHAR(10),

    CONSTRAINT fk_users_occupation
        FOREIGN KEY (occupation_id)
        REFERENCES occupations(occupation_id),

    CONSTRAINT chk_users_age
        CHECK (age > 0)
);

CREATE TABLE movies (
    movie_id INT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    release_date DATE,
    imdb_url VARCHAR(500)
);

CREATE TABLE movie_genres (
    movie_id INT NOT NULL,
    genre_id INT NOT NULL,

    PRIMARY KEY (movie_id, genre_id),

    CONSTRAINT fk_movie_genres_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id),

    CONSTRAINT fk_movie_genres_genre
        FOREIGN KEY (genre_id)
        REFERENCES genres(genre_id)
);

CREATE TABLE ratings (
    user_id INT NOT NULL,
    movie_id INT NOT NULL,
    rating TINYINT NOT NULL,
    timestamp BIGINT NOT NULL,

    PRIMARY KEY (user_id, movie_id),

    CONSTRAINT fk_ratings_user
        FOREIGN KEY (user_id)
        REFERENCES users(user_id),

    CONSTRAINT fk_ratings_movie
        FOREIGN KEY (movie_id)
        REFERENCES movies(movie_id),

    CONSTRAINT chk_ratings_value
        CHECK (rating BETWEEN 1 AND 5)
);
USE movielens;

INSERT INTO genres (genre_id, name) VALUES
(0, 'unknown'),
(1, 'Action'),
(2, 'Adventure'),
(3, 'Animation'),
(4, 'Children''s'),
(5, 'Comedy'),
(6, 'Crime'),
(7, 'Documentary'),
(8, 'Drama'),
(9, 'Fantasy'),
(10, 'Film-Noir'),
(11, 'Horror'),
(12, 'Musical'),
(13, 'Mystery'),
(14, 'Romance'),
(15, 'Sci-Fi'),
(16, 'Thriller'),
(17, 'War'),
(18, 'Western');

USE movielens;

INSERT INTO occupations (occupation_id, name) VALUES
(0, 'administrator'),
(1, 'artist'),
(2, 'doctor'),
(3, 'educator'),
(4, 'engineer'),
(5, 'entertainment'),
(6, 'executive'),
(7, 'healthcare'),
(8, 'homemaker'),
(9, 'lawyer'),
(10, 'librarian'),
(11, 'marketing'),
(12, 'none'),
(13, 'other'),
(14, 'programmer'),
(15, 'retired'),
(16, 'salesman'),
(17, 'scientist'),
(18, 'student'),
(19, 'technician'),
(20, 'writer');

USE movielens;

CREATE TABLE staging_users (
    user_id INT,
    age INT,
    gender CHAR(1),
    occupation VARCHAR(50),
    zip_code VARCHAR(10)
);

SELECT COUNT(*) FROM users;
SELECT
    u.user_id,
    u.age,
    u.gender,
    o.name AS occupation,
    u.zip_code
FROM users u
JOIN occupations o
    ON u.occupation_id = o.occupation_id
LIMIT 10;

SELECT
    m.movie_id,
    m.title,
    g.name AS genre
FROM movies m
JOIN movie_genres mg
    ON m.movie_id = mg.movie_id
JOIN genres g
    ON mg.genre_id = g.genre_id
WHERE m.movie_id = 1
ORDER BY g.genre_id;