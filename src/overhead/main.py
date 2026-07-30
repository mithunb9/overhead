from dotenv import load_dotenv

load_dotenv()

import logging  # noqa: E402
import os  # noqa: E402

from fastapi import FastAPI  # noqa: E402

from overhead.api.routes.overhead import router as overhead_router # noqa: E402
from overhead.clients.aeroapi import AEROAPI_KEY_ENV # noqa: E402
from overhead.config import settings # noqa: E402

logger = logging.getLogger(__name__)

app = FastAPI(title="overhead")

app.include_router(overhead_router)

if settings.overhead.route_source == "aeroapi" and not os.environ.get(AEROAPI_KEY_ENV):
    logger.warning(
        "route_source is 'aeroapi' but %s is not set; route enrichment will be skipped",
        AEROAPI_KEY_ENV,
    )
