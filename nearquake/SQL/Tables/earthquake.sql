CREATE SCHEMA earthquake;

CREATE TABLE IF NOT EXISTS earthquake.fct__event_details (
    ids VARCHAR(50) PRIMARY KEY NOT NULL,
    mag FLOAT,
    place_id INTEGER FOREIGN KEY,
    time_id INTEGER,
    updated TIMESTAMP,
    tz INTEGER,
    felt INTEGER,
    cdi FLOAT,
    mmi FLOAT,
    alert_id INTEGER FOREIGN KEY,
    status VARCHAR(50),
    tsunami BOOLEAN,
    type VARCHAR(50),
    title VARCHAR(200),
    date DATE
) PARTITION BY RANGE (date);

COMMENT ON COLUMN earthquake.fct__event_details.ids IS 'Earlthquake id Primary key';
COMMENT ON COLUMN earthquake.fct__event_details.mag IS 'Magnitude of the earthquake';
COMMENT ON COLUMN earthquake.fct__event_details.place_id IS 'Place id ';
COMMENT ON COLUMN earthquake.fct__event_details.time_id IS 'Time id ';
COMMENT ON COLUMN earthquake.fct__event_details.updated IS 'Timestamp of the last update';
COMMENT ON COLUMN earthquake.fct__event_details.tz IS 'Time zone';
COMMENT ON COLUMN earthquake.fct__event_details.felt IS 'Number of people who reported feeling the earthquake';
COMMENT ON COLUMN earthquake.fct__event_details.cdi IS 'Community Internet Intensity Map';
COMMENT ON COLUMN earthquake.fct__event_details.mmi IS 'Modified Mercalli Intensity';
COMMENT ON COLUMN earthquake.fct__event_details.alert_id IS 'Alert id';
COMMENT ON COLUMN earthquake.fct__event_details.status IS 'Status of the earthquake report';
COMMENT ON COLUMN earthquake.fct__event_details.tsunami IS 'Indicates if a tsunami was generated';
COMMENT ON COLUMN earthquake.fct__event_details.type IS 'Type of seismic event';
COMMENT ON COLUMN earthquake.fct__event_details.title IS 'Title of the earthquake event';
COMMENT ON COLUMN earthquake.fct__event_details.date IS 'Date of the earthquake';

CREATE TABLE IF NOT EXISTS earthquake.dim__place (
    place_id SERIAL PRIMARY KEY,
    place VARCHAR(200),
    detail VARCHAR(500)
);

COMMENT ON COLUMN earthquake.dim__place.place_id IS 'Primary key';
COMMENT ON COLUMN earthquake.dim__place.place IS 'Location of the earthquake';


CREATE TABLE IF NOT EXISTS earthquake.dim__time (
    time_id SERIAL PRIMARY KEY,
    time TIMESTAMP
);

COMMENT ON COLUMN earthquake.dim__time.time_id IS 'Primary key';
COMMENT ON COLUMN earthquake.dim__time.time IS 'Timestamp of the earthquake';

CREATE TABLE IF NOT EXISTS earthquake.dim__alert (
    alert_id SERIAL PRIMARY KEY,
    alert VARCHAR(50)
);

COMMENT ON COLUMN earthquake.dim__alert.alert_id IS 'Primary key';
COMMENT ON COLUMN earthquake.dim__alert.alert IS 'Alert level of the earthquake';

CREATE TABLE IF NOT EXISTS earthquake.dim__location_coordinates (
    ids varchar(50) PRIMARY KEY,
    longitude float,
    latitude float,
    depth float
);

COMMENT ON COLUMN earthquake.dim__location_coordinates.ids IS 'Primary key';
COMMENT ON COLUMN earthquake.dim__location_coordinates.longitude IS 'Longitude';
COMMENT ON COLUMN earthquake.dim__location_coordinates.latitude IS 'Latitude';
COMMENT ON COLUMN earthquake.dim__location_coordinates.depth IS 'Depth';

CREATE TABLE IF NOT EXISTS earthquake.fct__upload_date (
    uploadid  PRIMARY KEY,
    upload_date DATE,
    max_quake_date DATE,
);

COMMENT ON COLUMN earthquake.fct__upload_date.uploadid IS 'Unique id of the upload event ';
COMMENT ON COLUMN earthquake.fct__upload_date.upload_date IS 'The date the upload event occured ';
COMMENT ON COLUMN earthquake.fct__upload_date.max_quake_date IS 'The latest earthquake that occured on the upload date';
