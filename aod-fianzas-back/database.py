from psycopg2 import connect, sql, OperationalError
import dotenv
import os

dotenv.load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@db-alquileres-dev/postgres")
DB_TABLE = os.getenv("DB_TABLE", "fianzapos_2023")

def query_municipalities():
    query = """SELECT DISTINCT f.nombre_municipio 
                FROM fianzapos f 
                WHERE f.clave_calle IS NOT NULL 
                ORDER BY f.nombre_municipio ASC;"""
    with connect(DB_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(sql.SQL(query))
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
            cur.execute(sql.SQL("SELECT DISTINCT nombre_calle "
                                "FROM mv_fianzas_all_app_web f "
                                f"WHERE f.nombre_municipio = '{municipality}'"
                                " and f.clave_calle != ''"
                                " and f.anyo >= 1996"
                                "ORDER BY nombre_calle ASC"))
            results = cur.fetchall()
            streets = []
            for result in results:
                street = {
                    "nombre_calle": result[0]
                }
                streets.append(street)
    return streets

class DBException(Exception):
    message=""
    def __init__(self, message):
        self.message = message

def get_eslocal(eslocal: int) -> str:
    if eslocal == 1:
        return "Vivienda"
    elif eslocal == 2:
        return "Local"
    else:
        return "-"

def query_stats_by_street_and_municipality(street: str, municipality: str):
    query = "SELECT anyo,min_renta,max_renta,media_renta,eslocal,nfianzas,clave_calle "\
            "FROM mv_fianzas_all_app_web "\
            f"WHERE nombre_calle = '{street}' AND nombre_municipio = '{municipality}'"\
            " and clave_calle != '' " \
            " and  anyo > 1996" \
            " ORDER BY anyo DESC,eslocal DESC;"

    try:
        with connect(DB_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL(query))
                results = cur.fetchall()
                stats = []
                for result in results:
                    stat = {
                        "anyo": result[0],
                        "min_renta": result[1],
                        "max_renta": result[2],
                        "media_renta": result[3],
                        "eslocal": get_eslocal(result[4]),
                        "nfianzas": result[5],
                    }
                    stats.append(stat)
                return stats
    except OperationalError as e:
        raise DBException(str(e))