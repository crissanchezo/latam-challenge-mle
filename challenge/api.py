import logging
from contextlib import asynccontextmanager
from typing import List

import pandas as pd
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, field_validator

from challenge.model import DelayModel


logger = logging.getLogger("uvicorn.error")

VALID_OPERATORS: list[str] = []


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


class PredictRequest(BaseModel):
    flights: List[Flight]


@asynccontextmanager
async def lifespan(app: FastAPI):
    global VALID_OPERATORS

    logger.info("Application startup: Loading data...")
    data = pd.read_csv("data/data.csv")
    logger.info("Application startup: Data loaded, shape: %s", data.shape)

    VALID_OPERATORS = data["OPERA"].unique().tolist()
    logger.info("Application startup: Valid operators: %s", VALID_OPERATORS)

    logger.info("Application startup: Training model...")
    features, target = model.preprocess(data=data, target_column="delay")
    model.fit(features=features, target=target)
    logger.info("Application startup: Training complete")

    yield

    logger.info("Shutdown application...")


model = DelayModel()
app = FastAPI(lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    When Pydantic have an validation error,
    FastAPI throws RequestValidationError with HTTP 422 Unprocessable Entity.
    This method transform that to HTTP 400 Bad Request

    Args:
        request (Request): Request body.
        exc (RequestValidationError): FastAPI error.

    Return:
        JSONResponse: The response with the error.
    """
    return JSONResponse(status_code=400, content={"detail": str(exc)})


@app.get("/health", status_code=200)
async def get_health() -> dict:
    return {"status": "OK"}


@app.post("/predict", status_code=200)
async def post_predict(request: PredictRequest) -> dict:
    if not VALID_OPERATORS:
        logger.warning("OPERA validation skipped: operators list not loaded")
    else:
        for flight in request.flights:
            if flight.OPERA not in VALID_OPERATORS:
                raise RequestValidationError(
                    f"Flight {flight.OPERA} is not a valid operator"
                )

    flights_data = [flight.model_dump() for flight in request.flights]
    df = pd.DataFrame(flights_data)

    features = model.preprocess(data=df)
    predictions = model.predict(features=features)

    return {"predict": predictions}
