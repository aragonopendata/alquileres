DROP TABLE IF EXISTS opendata_usr.fianzas_app;
CREATE TABLE opendata_usr.fianzas_app AS
SELECT 
    f.c_mun_via,
    f.anyo,
    f.min_renta,
    f.max_renta,
    f.media_renta,
    f.eslocal,
    f.nfianzas,
    c.objectid,
    c.via_loc,
    c.nombre_calle,
    c.nombre_municipio
FROM opendata_usr.fianzas_all_app f
INNER JOIN opendata_usr.callejero c
    ON f.c_mun_via = c.c_mun_via
WHERE f.anyo >= 2000 AND f.anyo <= 2024;
CREATE INDEX idx_fianzas_app_nombre_municipio ON opendata_usr.fianzas_app(nombre_municipio);
