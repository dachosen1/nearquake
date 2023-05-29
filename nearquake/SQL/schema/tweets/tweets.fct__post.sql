CREATE TABLE IF NOT EXISTS tweets.fct__post (
    id_post VARCHAR(50) PRIMARY KEY,
    post VARCHAR(240),
    ts_upload_utc TIMESTAMP
);
COMMENT ON TABLE tweets.fct__post IS 'Table for storing tweet posts';
COMMENT ON COLUMN tweets.fct__post.id_post IS 'Primary key for each tweet';
COMMENT ON COLUMN tweets.fct__post.post IS 'Content of the tweet';
COMMENT ON COLUMN tweets.fct__post.ts_upload_utc IS 'Timestamp when the tweet was posted';