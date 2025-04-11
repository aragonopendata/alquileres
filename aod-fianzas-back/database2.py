from psycopg2 import connect, sql, OperationalError
import dotenv
import os
import pandas as pd

dotenv.load_dotenv()

DB_URL = os.getenv("DB_URL", "postgresql://postgres:postgres@db-alquileres-dev/postgres")
DB_TABLE = os.getenv("DB_TABLE", "fianzapos_2023")

def query_municipalities():
    df = pd.read_csv('callejero.csv')
    municipalities = df['nombre_municipio'].unique().tolist()
    municipalities = [m for m in municipalities if pd.notna(m)]  # Remove any NaN values
    municipalities.sort()  # Sort alphabetically
    return municipalities

def query_streets_by_municipality(municipality: str):
    df = pd.read_csv('callejero.csv')
    streets = df[df['nombre_municipio'] == municipality]['nombre_calle'].unique().tolist()
    streets = [s for s in streets if pd.notna(s)]  # Remove any NaN values
    streets.sort()  # Sort alphabetically
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
    # First get c_mun_via from CSV
    df = pd.read_csv('callejero.csv')
    c_mun_via = df[(df['nombre_calle'] == street) & (df['nombre_municipio'] == municipality)]['c_mun_via'].iloc[0]
    
    query = "SELECT anyo,min_renta,max_renta,media_renta,eslocal,nfianzas,clave_calle "\
            "FROM mv_fianzas_all_app_web "\
            f"WHERE c_mun_via = '{c_mun_via}'"\
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