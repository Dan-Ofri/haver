"""HTTP entry point."""

from typing import Annotated, Literal

from fastapi import Depends, FastAPI
from pydantic import BaseModel

from haver import db
from haver.config import Settings, get_settings


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok", "unavailable"]


def create_app() -> FastAPI:
    app = FastAPI(title="Haver API", version="0.1.0")

    @app.get("/api/health")
    def health(settings: Annotated[Settings, Depends(get_settings)]) -> HealthResponse:
        database = "ok" if db.ping(settings.database_url) else "unavailable"
        return HealthResponse(status="ok", database=database)

    return app


app = create_app()
