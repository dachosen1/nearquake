CREATE SCHEMA tweets;

CREATE TABLE IF NOT EXISTS tweets.fct__post (
    id VARCHAR(50) PRIMARY KEY,
    post VARCHAR(240),
    time TIMESTAMP
);

COMMENT ON TABLE tweets.fct__post IS 'Table for storing tweet posts';
COMMENT ON COLUMN tweets.fct__post.id IS 'Primary key for each tweet';
COMMENT ON COLUMN tweets.fct__post.post IS 'Content of the tweet';
COMMENT ON COLUMN tweets.fct__post.time IS 'Timestamp when the tweet was posted';