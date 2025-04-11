from venv import logger

from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse
import logging

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)

from database2 import query_municipalities, query_streets_by_municipality, \
    query_stats_by_street_and_municipality, DBException

app = FastAPI()


@app.get("/")
def root():
    return RedirectResponse(url="/docs")


@app.get("/municipality")
def get_municipalities():
    municipalities = query_municipalities()
    return municipalities


@app.get("/municipality/{municipality}/street")
def get_streets_by_municipality(municipality: str):
    streets = query_streets_by_municipality(municipality)
    return streets

@app.get("/municipality/{municipality}/street/{street}/stats")
def get_stats_by_municipality_street(municipality: str, street: str):
    try:
        stats = query_stats_by_street_and_municipality(street, municipality)
    except DBException as e:
        logger.error(e.message)
        raise HTTPException(status_code=500, detail="DB error")
    return stats
