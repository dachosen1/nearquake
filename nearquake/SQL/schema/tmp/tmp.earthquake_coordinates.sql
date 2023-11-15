CREATE TABLE IF NOT EXISTS tmp.earthquake_coordinates (
    ids VARCHAR(50) PRIMARY KEY,
    longitude FLOAT,
    latitude FLOAT,
    depth FLOAT
);
COMMENT ON COLUMN earthquake.dim__location_coordinates.ids IS 'Primary key';
COMMENT ON COLUMN earthquake.dim__location_coordinates.longitude IS 'Longitude';
COMMENT ON COLUMN earthquake.dim__location_coordinates.latitude IS 'Latitude';
COMMENT ON COLUMN earthquake.dim__location_coordinates.depth IS 'Depth';
