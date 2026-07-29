from fastapi import FastAPI

from flights_api.api.routes.overhead import router as overhead_router

app = FastAPI(title="flights-api")

app.include_router(overhead_router)
