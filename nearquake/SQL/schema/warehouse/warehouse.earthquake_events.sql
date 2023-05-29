CREATE TABLE IF NOT EXISTS warehouse.earthquake_events (
    ids VARCHAR(50) PRIMARY KEY,
    mag FLOAT,
    place VARCHAR(200),
    time BIGINT,
    updated TIMESTAMP,
    tz INTEGER,
    felt INTEGER,
    cdi FLOAT,
    mmi FLOAT,
    alert VARCHAR(50),
    status VARCHAR(50),
    tsunami BOOLEAN,
    type VARCHAR(50),
    title VARCHAR(200),
    upload_time TIMESTAMP
);
COMMENT ON TABLE warehouse.earthquake_events IS 'Table for storing earthquake event data';
COMMENT ON COLUMN warehouse.earthquake_events.ids IS 'Unique identifier for each earthquake event';
COMMENT ON COLUMN warehouse.earthquake_events.mag IS 'Magnitude of the earthquake';
COMMENT ON COLUMN warehouse.earthquake_events.place IS 'Location where the earthquake occurred';
COMMENT ON COLUMN warehouse.earthquake_events.time IS 'Timestamp of when the earthquake event happened in miliseconds';
COMMENT ON COLUMN warehouse.earthquake_events.updated IS 'Timestamp of when the earthquake event was last updated in miliseconds';
COMMENT ON COLUMN warehouse.earthquake_events.tz IS 'Timezone offset';
COMMENT ON COLUMN warehouse.earthquake_events.felt IS 'Count of felt reports';
COMMENT ON COLUMN warehouse.earthquake_events.cdi IS 'Community Internet Intensity Map value';
COMMENT ON COLUMN warehouse.earthquake_events.mmi IS 'Modified Mercalli Intensity value';
COMMENT ON COLUMN warehouse.earthquake_events.alert IS 'Alert level of the earthquake';
COMMENT ON COLUMN warehouse.earthquake_events.status IS 'Status description of the earthquake';
COMMENT ON COLUMN warehouse.earthquake_events.tsunami IS 'Indicates if the earthquake event caused a tsunami';
COMMENT ON COLUMN warehouse.earthquake_events.type IS 'Type of the earthquake event';
COMMENT ON COLUMN warehouse.earthquake_events.title IS 'Title or summary of the earthquake event';
COMMENT ON COLUMN warehouse.earthquake_events.upload_time IS 'The timestamp of when the event was uploaded to the warehouse';
