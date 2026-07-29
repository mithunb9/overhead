from fastapi import FastAPI

from overhead.api.routes.overhead import router as overhead_router

app = FastAPI(title="overhead")

app.include_router(overhead_router)
