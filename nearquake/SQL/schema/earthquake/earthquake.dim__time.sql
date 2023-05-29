CREATE TABLE IF NOT EXISTS earthquake.dim__time (
    id_time INTEGER PRIMARY KEY,
    ts_event_utc TIMESTAMP
);
COMMENT ON COLUMN earthquake.dim__time.id_time IS 'Primary key';
COMMENT ON COLUMN earthquake.dim__time.ts_event_utc IS 'Timestamp of the earthquake';
