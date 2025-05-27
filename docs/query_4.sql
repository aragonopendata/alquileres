DROP TABLE IF EXISTS opendata_usr.fianzapos_app;
CREATE TABLE opendata_usr.fianzapos_app AS
	SELECT fianzapos_2024.anyo, fianzapos_2024.codigo_provincia,
		fianzapos_2024.clave_calle, fianzapos_2024.nombre_calle,
		fianzapos_2024.nombre_municipio, fianzapos_2024.tipo,
		fianzapos_2024.anyo_devolucion, fianzapos_2024.total_rentas_str,
		fianzapos_2024.total_importes, fianzapos_2024.total_devolucion,
		fianzapos_2024.total_rentas
	FROM opendata_usr.fianzapos_2024 fianzapos_2024;

DROP TABLE IF EXISTS opendata_usr.fianzapos_data_app;
CREATE TABLE opendata_usr.fianzapos_data_app AS 
 SELECT DISTINCT fianzapos_app.anyo, fianzapos_app.codigo_provincia, fianzapos_app.clave_calle, 
    fianzapos_app.nombre_calle, fianzapos_app.nombre_municipio, fianzapos_app.tipo, 
    fianzapos_app.anyo_devolucion, fianzapos_app.total_rentas_str, 
    fianzapos_app.total_importes, fianzapos_app.total_devolucion, 
    fianzapos_app.total_rentas, fianzapos.c_mun_via
   FROM opendata_usr.fianzapos_app, fianzapos
  WHERE (replace((fianzapos_app.nombre_calle::text || '@@@'::text) || fianzapos_app.nombre_municipio::text, '"'::text, ''::text) IN ( SELECT (fianzapos.nombre_calle_orig::text || '@@@'::text) || fianzapos.nombre_municipio_orig::text
           FROM fianzapos)) AND fianzapos.nombre_calle_orig::text = replace(fianzapos_app.nombre_calle::text, '"'::text, ''::text) AND fianzapos.nombre_municipio_orig::text = replace(fianzapos_app.nombre_municipio::text, '"'::text, ''::text);

DROP TABLE IF EXISTS opendata_usr.fianzas_all_app;
CREATE TABLE opendata_usr.fianzas_all_app AS 
 SELECT fianzapos.c_mun_via, fianzapos.anyo, 
    min(fianzapos.total_rentas) AS min_renta, 
    max(fianzapos.total_rentas) AS max_renta, 
    round(avg(fianzapos.total_rentas), 2) AS media_renta, 
        CASE btrim(fianzapos.tipo::text)
            WHEN 'Vivienda'::text THEN 1
            ELSE 2
        END AS eslocal, 
    count(*) AS nfianzas
   FROM opendata_usr.fianzapos_data_app fianzapos
  GROUP BY fianzapos.anyo, fianzapos.c_mun_via, eslocal
  ORDER BY fianzapos.c_mun_via;