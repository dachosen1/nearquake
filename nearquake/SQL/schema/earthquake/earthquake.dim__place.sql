CREATE TABLE IF NOT EXISTS earthquake.dim__place (
    id_place INTEGER PRIMARY KEY,
    place VARCHAR(200)
);
COMMENT ON COLUMN earthquake.dim__place.id_place IS 'Primary key';
COMMENT ON COLUMN earthquake.dim__place.place IS 'Location of the earthquake';