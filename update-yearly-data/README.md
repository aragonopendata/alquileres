# update-yearly-data

One-off script to load a new year's rental deposit data into the remote PostgreSQL database. Run once a year after the source data is published on opendata.aragon.es.

## What it does

1. Downloads the full CSV from opendata.aragon.es (~45 MB, may take ~2 min)
2. Creates `opendata_usr.fianzapos_<year>`
3. Loads the CSV rows via `COPY`
4. Adds and populates the `total_rentas_str` column
5. Creates views `v_fianzapos_<year>`, `v_fianzapos_data_<year>`, `v_fianzas_all_<year>`

## Requirements

- Docker

## Usage

```bash
# Build the image (once)
docker build -t update-yearly-data .

# Run for a given year
docker run --rm -e DATABASE_URL="postgresql://user:pass@host:5432/db" update-yearly-data 2025
```

To skip the download if you already have the CSV (mount it into the container):

```bash
docker run --rm \
  -e DATABASE_URL="postgresql://user:pass@host:5432/db" \
  -v "$(pwd)/fianzapos_2025.csv:/app/fianzapos_2025.csv" \
  update-yearly-data 2025 --skip-download
```

## Notes

- The `fianzapos` table (without year suffix) must already exist in the database — it is used as a lookup for street/municipality matching in the views.
- The script is idempotent for the table creation (`CREATE TABLE IF NOT EXISTS`) but will fail on duplicate rows if run twice. Drop the table and views first if you need to re-run.
