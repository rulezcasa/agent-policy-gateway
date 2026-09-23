from contextlib import asynccontextmanager

from fastapi import FastAPI

from .agents.state import init_state
from .api.router import router as business_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_state()
    yield


app = FastAPI(
    title="Maplewood Home & Living Business API",
    version="1.0.0",
    description="Demo business-system endpoints for Maplewood Home & Living.",
    lifespan=lifespan,
)
app.include_router(business_router, prefix="/api")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        app,
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
