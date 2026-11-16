from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.db import init_db
from service2.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db("incidents")
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
