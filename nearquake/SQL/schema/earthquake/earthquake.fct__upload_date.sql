CREATE TABLE IF NOT EXISTS earthquake.fct__upload_date (
    uploadid INTEGER PRIMARY KEY,
    upload_date DATE,
    max_quake_date DATE
);
COMMENT ON COLUMN earthquake.fct__upload_date.uploadid IS 'Unique id of the upload event ';
COMMENT ON COLUMN earthquake.fct__upload_date.upload_date IS 'The date the upload event occured ';
COMMENT ON COLUMN earthquake.fct__upload_date.max_quake_date IS 'The latest earthquake that occured on the upload date';
