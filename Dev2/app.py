#small fastapi web server
#app.py for FastAPI routes
import os
from contextlib import asynccontextmanager
from pathlib import Path
 
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import uvicorn
 
from db import init_db
from incidents.routes import router as incidents_router
from password.repository import seed_default_rules, seed_weak_passwords
from password.routes import router as password_router

from fastapi.middleware.cors import CORSMiddleware

BASE_DIR = Path(__file__).resolve().parent #This finds the folder containing app.py
'''
__file__ is the path to the current Python file
.resolve() converts it into an absolute path
.parent gets the containing folder
'''
PORT = int(os.getenv("PORT", "8000"))

app = FastAPI() #creates the web application, object stores your routes and handles incoming browser requests
#FastAPI is a Python framework that handles HTTP requests and responses.
#This tells FastAPI/Jinja2 where your HTML files live or where to look for them. The directory is set to the templates folder inside the src folder.:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "templates"))

#Static files are mounted, This line makes /static serve files from a folder:
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "src" / "static")), name="static") #Configuring static files

app.include_router(incidents_router)
app.include_router(password_router)

#The route is defined using the @app.get("/") decorator, which means that this function will be called when a GET request is made to the root URL ("/") of the application.
#Defining the homepage
@app.get("/") #tells FastAPI: “when someone visits the root URL /, run this function”
def home(request: Request): #request contains the browser request information
    return templates.TemplateResponse( #TemplateResponse loads the HTML template file base.html
        request=request,
        name="home.html",
        context={"request": request}, #the browser gets the rendered HTML page back
    )
'''
So when you open: http://localhost:8001/ the function runs and returns the HTML page.
'''


if __name__ == "__main__":
    init_db() #initialize SQLite before starging the server
    print(seed_weak_passwords())
    uvicorn.run(app, host="0.0.0.0", port=PORT) #This line starts the server:


'''
source /Users/Laura/venvs/myapp/bin/activate
cd /Users/Laura
python3 /Users/Laura/Desktop/app.py
'''

'''
This is the request flow:

1. Browser requests http://localhost:8001/
2. FastAPI route / matches
3. home() function runs
4. It loads base.html
5. The HTML is returned to the browser
6. Browser renders it and shows:
Hello from FastAPI
'''
