"""
Load a new year's rental deposit data into the remote database.

Usage:
    uv run update_yearly_data.py [year] [--skip-download]

    year             Year to process (default: 2025)
    --skip-download  Skip download and reuse fianzapos_<year>.csv if present

Environment:
    DATABASE_URL     PostgreSQL connection URL (required)

Example:
    export DATABASE_URL=postgresql://user:pass@host:5432/dbname
    uv run update_yearly_data.py 2025
"""

import argparse
import io
import logging
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path

import httpx
import pandas as pd
import psycopg2
from psycopg2 import sql

logging.basicConfig(level=logging.INFO, format="%(asctime)s  %(message)s", datefmt="%H:%M:%S")
log = logging.getLogger(__name__)

CSV_URL = "https://opendata.aragon.es/GA_OD_Core/download?resource_id=100&format=csv"
SCHEMA = "opendata_usr"

CSV_COLUMNS = [
    "anyo",
    "codigo_provincia",
    "clave_calle",
    "nombre_calle",
    "nombre_municipio",
    "tipo",
    "anyo_devolucion",
    "total_rentas",
    "total_importes",
    "total_devolucion",
]

TOTAL_STEPS = 5


@contextmanager
def step(n: int, description: str):
    log.info("─" * 60)
    log.info("[%d/%d] %s", n, TOTAL_STEPS, description)
    t0 = time.perf_counter()
    yield
    elapsed = time.perf_counter() - t0
    log.info("      done in %.1fs", elapsed)


# ---------------------------------------------------------------------------
# Step 1: download
# ---------------------------------------------------------------------------

def download_csv(dest: Path) -> None:
    log.info("      URL: %s", CSV_URL)
    log.info("      This may take up to 2 minutes for the full dataset...")

    timeout = httpx.Timeout(connect=30.0, read=300.0, write=30.0, pool=5.0)
    total_bytes = 0
    last_logged_mb = 0.0
    TICK_MB = 5.0

    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        with client.stream("GET", CSV_URL) as response:
            response.raise_for_status()
            with open(dest, "wb") as f:
                for chunk in response.iter_bytes(chunk_size=65536):
                    f.write(chunk)
                    total_bytes += len(chunk)
                    current_mb = total_bytes / 1024 / 1024
                    if current_mb - last_logged_mb >= TICK_MB:
                        log.info("      %.0f MB downloaded...", current_mb)
                        last_logged_mb = current_mb

    log.info("      %.1f MB saved to %s", total_bytes / 1024 / 1024, dest)


# ---------------------------------------------------------------------------
# Step 2: create table
# ---------------------------------------------------------------------------

def create_table(conn, year: int) -> None:
    log.info("      Table: %s.fianzapos_%d", SCHEMA, year)
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL(
                """
                CREATE TABLE IF NOT EXISTS {schema}.{table} (
                    anyo                integer,
                    codigo_provincia    character varying(255),
                    clave_calle         character varying(255),
                    nombre_calle        character varying(255),
                    nombre_municipio    character varying(255),
                    tipo                character varying(255),
                    anyo_devolucion     character varying(255),
                    total_rentas        numeric,
                    total_importes      character varying(255),
                    total_devolucion    character varying(255)
                )
                """
            ).format(
                schema=sql.Identifier(SCHEMA),
                table=sql.Identifier(f"fianzapos_{year}"),
            )
        )
    conn.commit()
    log.info("      Table created (or already existed)")


# ---------------------------------------------------------------------------
# Step 3: load CSV via COPY (fast path)
# ---------------------------------------------------------------------------

def load_csv(conn, year: int, csv_path: Path) -> None:
    log.info("      Reading %s...", csv_path)
    df = pd.read_csv(csv_path, usecols=CSV_COLUMNS, dtype=str)
    df = df.where(pd.notna(df), "")
    log.info("      %d rows read from CSV", len(df))

    log.info("      Streaming into %s.fianzapos_%d via COPY...", SCHEMA, year)
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=True)
    buf.seek(0)

    qualified = f"{SCHEMA}.fianzapos_{year}"
    cols = ", ".join(CSV_COLUMNS)
    with conn.cursor() as cur:
        cur.copy_expert(
            f"COPY {qualified} ({cols}) FROM STDIN WITH CSV HEADER NULL ''",
            buf,
        )
    conn.commit()
    log.info("      %d rows loaded", len(df))


# ---------------------------------------------------------------------------
# Step 4: add total_rentas_str
# ---------------------------------------------------------------------------

def add_total_rentas_str(conn, year: int) -> None:
    table = f"{SCHEMA}.fianzapos_{year}"
    log.info("      ALTER TABLE %s ADD COLUMN total_rentas_str", table)
    with conn.cursor() as cur:
        cur.execute(
            f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS total_rentas_str character varying(255)"
        )
        log.info("      UPDATE total_rentas_str = CAST(total_rentas ...)")
        cur.execute(
            f"UPDATE {table} SET total_rentas_str = CAST(total_rentas AS character varying(255))"
        )
    conn.commit()
    log.info("      Column populated")


# ---------------------------------------------------------------------------
# Step 5: create views
# ---------------------------------------------------------------------------

def create_views(conn, year: int) -> None:
    s = SCHEMA

    views = [
        (
            f"v_fianzapos_{year}",
            f"""
            SELECT f.anyo, f.codigo_provincia, f.clave_calle, f.nombre_calle,
                   f.nombre_municipio, f.tipo, f.anyo_devolucion,
                   f.total_rentas_str, f.total_importes, f.total_devolucion,
                   f.total_rentas
            FROM {s}.fianzapos_{year} f
            WHERE f.anyo = {year}
            """,
        ),
        (
            f"v_fianzapos_data_{year}",
            f"""
            SELECT DISTINCT
                v.anyo, v.codigo_provincia, v.clave_calle, v.nombre_calle,
                v.nombre_municipio, v.tipo, v.anyo_devolucion,
                v.total_rentas_str, v.total_importes, v.total_devolucion,
                v.total_rentas, fp.c_mun_via
            FROM {s}.v_fianzapos_{year} v, fianzapos fp
            WHERE
                replace((v.nombre_calle::text || '@@@') || v.nombre_municipio::text, '"', '')
                IN (
                    SELECT (fp2.nombre_calle_orig::text || '@@@') || fp2.nombre_municipio_orig::text
                    FROM fianzapos fp2
                )
                AND fp.nombre_calle_orig::text = replace(v.nombre_calle::text, '"', '')
                AND fp.nombre_municipio_orig::text = replace(v.nombre_municipio::text, '"', '')
            """,
        ),
        (
            f"v_fianzas_all_{year}",
            f"""
            SELECT
                fp.c_mun_via,
                fp.anyo,
                min(fp.total_rentas)           AS min_renta,
                max(fp.total_rentas)           AS max_renta,
                round(avg(fp.total_rentas), 2) AS media_renta,
                CASE btrim(fp.tipo::text)
                    WHEN 'Vivienda' THEN 1
                    ELSE 2
                END AS eslocal,
                count(*) AS nfianzas
            FROM {s}.v_fianzapos_data_{year} fp
            GROUP BY fp.anyo, fp.c_mun_via, eslocal
            ORDER BY fp.c_mun_via
            """,
        ),
    ]

    with conn.cursor() as cur:
        for view_name, body in views:
            log.info("      Creating %s.%s", s, view_name)
            cur.execute(f"CREATE OR REPLACE VIEW {s}.{view_name} AS {body}")
            log.info("      OK")
    conn.commit()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("year", nargs="?", type=int, default=2025)
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip download, reuse fianzapos_<year>.csv in the current directory",
    )
    args = parser.parse_args()

    year = args.year
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        log.error("DATABASE_URL environment variable is not set")
        sys.exit(1)

    log.info("=" * 60)
    log.info("  Yearly data update — year %d", year)
    log.info("=" * 60)

    t_start = time.perf_counter()
    csv_path = Path(f"fianzapos_{year}.csv")

    with step(1, "Download CSV"):
        if args.skip_download:
            if not csv_path.exists():
                log.error("--skip-download set but %s not found", csv_path)
                sys.exit(1)
            log.info("      Skipped — using %s", csv_path)
        else:
            try:
                download_csv(csv_path)
            except Exception as e:
                log.error("      CSV download failed: %s", e)
                sys.exit(1)

    log.info("      Connecting to database...")
    try:
        conn = psycopg2.connect(db_url)
        log.info("      Connected")
    except Exception as e:
        log.error("      Database connection failed: %s", e)
        sys.exit(1)

    try:
        with step(2, "Create table"):
            create_table(conn, year)

        with step(3, "Load CSV data"):
            load_csv(conn, year, csv_path)

        with step(4, "Add total_rentas_str column"):
            add_total_rentas_str(conn, year)

        with step(5, "Create views"):
            create_views(conn, year)

    except Exception as e:
        conn.rollback()
        log.error("FAILED: %s", e)
        raise
    finally:
        conn.close()

    total_elapsed = time.perf_counter() - t_start
    log.info("─" * 60)
    log.info("  All done in %dm %ds", int(total_elapsed // 60), int(total_elapsed % 60))
    log.info("=" * 60)


if __name__ == "__main__":
    main()
