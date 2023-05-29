CREATE TABLE IF NOT EXISTS earthquake.fct__event_details (
    id_event VARCHAR(50) PRIMARY KEY,
    mag FLOAT,
    id_place INTEGER,
    id_time INTEGER,
    ts_updated_utc TIMESTAMP,
    tz INTEGER,
    felt INTEGER,
    detail VARCHAR(500),
    cdi FLOAT,
    mmi FLOAT,
    id_alert INTEGER,
    status VARCHAR(50),
    tsunami BOOLEAN,
    type VARCHAR(50),
    title VARCHAR(200),
    date DATE,
    FOREIGN KEY (id_place) REFERENCES earthquake.dim__place(id_place),
    FOREIGN KEY (id_alert) REFERENCES earthquake.dim__alert(id_alert),
    FOREIGN KEY (id_time) REFERENCES earthquake.dim__time(id_time)
);
COMMENT ON COLUMN earthquake.fct__event_details.ids IS 'Earlthquake id Primary key';
COMMENT ON COLUMN earthquake.fct__event_details.mag IS 'Magnitude of the earthquake';
COMMENT ON COLUMN earthquake.fct__event_details.id_place IS 'Place id ';
COMMENT ON COLUMN earthquake.fct__event_details.id_time IS 'Time id ';
COMMENT ON COLUMN earthquake.fct__event_details.updated IS 'Timestamp of the last update';
COMMENT ON COLUMN earthquake.fct__event_details.tz IS 'Time zone';
COMMENT ON COLUMN earthquake.fct__event_details.felt IS 'Number of people who reported feeling the earthquake';
COMMENT ON COLUMN earthquake.fct__event_details.cdi IS 'Community Internet Intensity Map';
COMMENT ON COLUMN earthquake.fct__event_details.mmi IS 'Modified Mercalli Intensity';
COMMENT ON COLUMN earthquake.fct__event_details.id_alert IS 'Alert id';
COMMENT ON COLUMN earthquake.fct__event_details.status IS 'Status of the earthquake report';
COMMENT ON COLUMN earthquake.fct__event_details.tsunami IS 'Indicates if a tsunami was generated';
COMMENT ON COLUMN earthquake.fct__event_details.type IS 'Type of seismic event';
COMMENT ON COLUMN earthquake.fct__event_details.title IS 'Title of the earthquake event';
COMMENT ON COLUMN earthquake.fct__event_details.date IS 'Date of the earthquake';