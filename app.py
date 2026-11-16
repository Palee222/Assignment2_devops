#small fastapi web server
#app.py for FastAPI routes
import os
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit
 
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import uvicorn
 
from db.db import init_db
from incidents.routes import router as incidents_router
from password.routes import router as password_router

from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent #This finds the folder containing app.py
'''
__file__ is the path to the current Python file
.resolve() converts it into an absolute path
.parent gets the containing folder
'''
PORT = int(os.getenv("PORT", "8000"))


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def get_cors_allowed_origins():
    configured_origins = os.getenv("CORS_ALLOWED_ORIGINS")
    if configured_origins is None:
        return ["http://localhost:5173", "http://127.0.0.1:5173"]

    origins = [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.netloc
            or parsed.path not in {"", "/"}
            or parsed.query
            or parsed.fragment
            or parsed.username
            or parsed.password
            or "*" in origin
        ):
            raise ValueError(
                f"Invalid CORS origin {origin!r}; configure scheme and host only."
            )
    return origins


app = FastAPI(lifespan=lifespan) #creates the web application, object stores your routes and handles incoming browser requests
#FastAPI is a Python framework that handles HTTP requests and responses.
#This tells FastAPI/Jinja2 where your HTML files live or where to look for them. The directory is set to the templates folder inside the src folder.:
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_allowed_origins(),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "templates"))

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "src" / "static")), name="static") #Configuring static files

app.include_router(incidents_router)
app.include_router(password_router)

@app.get("/") #tells FastAPI: “when someone visits the root URL /, run this function”
def home(request: Request): #request contains the browser request information
    return templates.TemplateResponse( #TemplateResponse loads the HTML template file base.html
        request=request,
        name="home.html",
        context={"request": request}, #the browser gets the rendered HTML page back
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=PORT) #This line starts the server:


