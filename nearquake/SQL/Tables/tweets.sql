CREATE SCHEMA tweets;

CREATE TABLE IF NOT EXISTS tweets.fct__post (
    id VARCHAR(50),
    post VARCHAR(240),
    time TIMESTAMP
);
