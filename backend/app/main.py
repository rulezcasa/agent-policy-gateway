from fastapi import FastAPI

from .api.business import router as business_router
from .gateway.gateway import router as gateway_router

app = FastAPI(
    title="Maplewood Home & Living Business API",
    version="1.0.0",
    description="Demo business-system endpoints called behind the policy gateway.",
)
app.include_router(business_router)
app.include_router(gateway_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import os
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
    )
