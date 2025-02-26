from fastapi import FastAPI
from starlette.responses import RedirectResponse

from database import query_municipalities, query_streets_by_municipality, query_fianzas_by_municipality_street

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


@app.get("/municipality/{municipality}/street/{street}")
def get_fianzas_by_municipality_street(municipality: str, street: str):
    fianzas = query_fianzas_by_municipality_street(municipality, street)
    return fianzas