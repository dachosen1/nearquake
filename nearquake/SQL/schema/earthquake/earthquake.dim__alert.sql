CREATE TABLE IF NOT EXISTS earthquake.dim__alert (
    id_alrert INTEGER PRIMARY KEY,
    alert VARCHAR(50)
);
COMMENT ON COLUMN earthquake.dim__alert.id_alrert IS 'Primary key';
COMMENT ON COLUMN earthquake.dim__alert.alert IS 'Alert level of the earthquake';
