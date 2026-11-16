from contextlib import asynccontextmanager

from fastapi import FastAPI

from db.db import init_db
from password.repository import seed_weak_passwords
from service1.routes import router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db("password")
    seed_weak_passwords()
    yield


app = FastAPI(lifespan=lifespan)
app.include_router(router)
