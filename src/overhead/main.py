import logging
import os

from fastapi import FastAPI

from overhead.api.routes.overhead import router as overhead_router
from overhead.clients.aeroapi import AEROAPI_KEY_ENV
from overhead.config import settings

logger = logging.getLogger(__name__)

app = FastAPI(title="overhead")

app.include_router(overhead_router)

if settings.overhead.route_source == "aeroapi" and not os.environ.get(AEROAPI_KEY_ENV):
    logger.warning(
        "route_source is 'aeroapi' but %s is not set; route enrichment will be skipped",
        AEROAPI_KEY_ENV,
    )
