from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI  # noqa: E402

from overhead.api.routes.overhead import router as overhead_router  # noqa: E402

app = FastAPI(title="overhead")

app.include_router(overhead_router)
