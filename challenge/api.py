from typing import List

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator

from challenge.model import DelayModel


VALID_OPERATORS = [
    "Grupo LATAM", "Sky Airline", "Aerolineas Argentinas", "Copa Air",
    "Latin American Wings", "Avianca", "JetSmart SPA", "Gol Trans",
    "American Airlines", "Air Canada", "Iberia", "Delta Air",
    "Air France", "Aeromexico", "United Airlines", "Oceanair Linhas Aereas",
    "Alitalia", "K.L.M.", "British Airways", "Qantas Airways",
    "Lacsa", "Austral", "Plus Ultra Lineas Aereas"
]


class Flight(BaseModel):
    OPERA: str
    TIPOVUELO: str
    MES: int

    @field_validator("MES")
    @classmethod
    def validate_mes(cls, v: int) -> int:
        if v < 1 or v > 12:
            raise ValueError("MES must be between 1 and 12")
        return v

    @field_validator("TIPOVUELO")
    @classmethod
    def validate_tipovuelo(cls, v: str) -> str:
        if v not in ["I", "N"]:
            raise ValueError("TIPOVUELO must be 'I' or 'N'")
        return v

    @field_validator("OPERA")
    @classmethod
    def validate_opera(cls, v: str) -> str:
        if v not in VALID_OPERATORS:
            raise ValueError(f"OPERA '{v}' is not a valid operator")
        return v


class PredictRequest(BaseModel):
    flights: List[Flight]


model = DelayModel()
app = FastAPI()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )


@app.on_event("startup")
async def startup_event():
    print(">>> STARTUP: Training model...")
    
    try:
        data = pd.read_csv("data/data.csv")
        print(f">>> STARTUP: Data loaded, shape: {data.shape}")
        features, target = model.preprocess(data=data, target_column="delay")
        model.fit(features=features, target=target)
        print(">>> STARTUP: Training complete")
    except Exception as e:
        print(f">>> STARTUP ERROR: {e}")


@app.get("/health", status_code=200)
async def get_health() -> dict:
    return {
        "status": "OK"
    }


@app.post("/predict", status_code=200)
async def post_predict(request: PredictRequest) -> dict:

    flights_data = [flight.model_dump() for flight in request.flights]
    df = pd.DataFrame(flights_data)
    
    features = model.preprocess(data=df)
    predictions = model.predict(features=features)

    return {"predict": predictions}