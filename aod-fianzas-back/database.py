from psycopg2 import connect, sql
import dotenv
import os

dotenv.load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@db-alquileres-dev/postgres")
DB_TABLE = os.getenv("DB_TABLE", "fianzapos_2023")

def query_municipalities():
    with connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL(f"SELECT DISTINCT nombre_municipio FROM {DB_TABLE} ORDER BY nombre_municipio ASC"))
            results = cur.fetchall()
            municipalities = []
            for result in results:
                municipality = {
                    "nombre_municipio": result[0]
                }
                municipalities.append(municipality)
    return municipalities


def query_streets_by_municipality(municipality: str):
    with connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL(f"SELECT DISTINCT nombre_calle "
                                f"FROM fianzapos_2023 "
                                f"WHERE nombre_municipio = '{municipality}' "
                                f"ORDER BY nombre_calle ASC"))
            results = cur.fetchall()
            streets = []
            for result in results:
                street = {
                    "nombre_calle": result[0]
                }
                streets.append(street)
    return streets

def query_fianzas_by_municipality_street(municipality: str, street: str):
    with connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL(
                "SELECT anyo, codigo_provincia, clave_calle, nombre_calle, nombre_municipio, tipo, anyo_devolucion, total_rentas_str, total_importes, total_devolucion, total_rentas "
                "FROM fianzapos_2023 "
                "WHERE nombre_municipio = %s "
                "AND nombre_calle = %s"), [municipality, street])
            results = cur.fetchall()
            fianzas = []
            for result in results:
                fianza = {
                    "anyo": result[0],
                    "codigo_provincia": result[1],
                    "clave_calle": result[2],
                    "nombre_calle": result[3],
                    "nombre_municipio": result[4],
                    "tipo": result[5],
                    "anyo_devolucion": result[6],
                    "total_rentas_str": result[7],
                    "total_importes": result[8],
                    "total_devolucion": result[9],
                    "total_rentas": result[10]
                }
                fianzas.append(fianza)
            print(fianzas)
    return fianzas

def query_street_id_by_street_name_and_municipality(street_name: str, municipality: str):
    query = f"select c_mun_via from v_fianzapos_data_2023 where nombre_calle = '{street_name}' and nombre_municipio =  '{municipality}';"
    with connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL(query))
            results = cur.fetchall()
            if len(results) > 1:
                raise Exception("More than one street_id found")
            elif len(results) == 0:
                return None
            else:
                return results[0][0]


def query_stats_by_street_id(street_id: str):
    query = "SELECT c_mun_via,anyo,min_renta,max_renta,media_renta,eslocal,nfianzas "\
            "FROM v_fianzas_all "\
            f"WHERE c_mun_via = '{street_id}' "\
            "ORDER BY anyo DESC;"
    with connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL(query))
            results = cur.fetchall()
            stats = []
            for result in results:
                stat = {
                    "c_mun_via": result[0],
                    "anyo": result[1],
                    "min_renta": result[2],
                    "max_renta": result[3],
                    "media_renta": result[4],
                    "eslocal": result[5],
                    "nfianzas": result[6],
                }
                stats.append(stat)
            return stats