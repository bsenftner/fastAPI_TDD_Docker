
from typing import Union

from fastapi import FastAPI, APIRouter, HTTPException, Request, Depends, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from pathlib import Path

from app.db import engine, database, metadata
from app.api import blogposts, notes, users, ping, crud 

# page_frag.py contains common page fragments, like .header & .footer.
# This is passed to page templates for repeated use of common html fragments: 
from app.page_frags import FRAGS 


# Project Directories
ROOT = Path(__file__).resolve().parent.parent
BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates")) 

# create db tables if they don't already exist:
metadata.create_all(engine)

# generate our "app"
app = FastAPI(title="FastAPI_TDD_Docker (& postgresql): Notes and BlogPosts", openapi_url="/openapi.json")

# add CORS handling: 
app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,
    )
    
# enable automatic serving of contents of "static" directory: 
app.mount("/static", StaticFiles(directory=str(BASE_PATH / "static")), name="static") 

# setup handler for application start that inits the db connection: 
@app.on_event("startup")
async def startup():
    await database.connect()

# setup handler for application shutdown that disconnects the db: 
@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()
    
    
# install the ping router into our app:
app.include_router(ping.router)

# install the notes router into our app;
# note the prefix URL along with the "notes" tag, 
# the prefix places the routes defined by notes.router after "/notes",
# these are also used by OpenAPI (for grouping operations).
app.include_router(notes.router, prefix="/notes", tags=["notes"])

# install the blogposts router into our app with a prefix & tag too:
app.include_router(blogposts.router, prefix="/blogposts", tags=["blogposts"])

# install the users router into our app with a prefix & tag too:
app.include_router(users.router, tags=["users"])


# define a router for the html returning endpoints: 
router = APIRouter()

# ------------------------------------------------------------------------------------------------------------------
# added to get favicon served:
favicon_path = BASE_PATH / 'favicon.ico'
@router.get("/favicon.ico", status_code=200, include_in_schema=False) 
def favicon():
    """
    Favicon.ico GET
    """
    # print(f"favicon_path is {favicon_path}")
    return FileResponse(favicon_path)


# ------------------------------------------------------------------------------------------------------------------
# serve homepage thru a Jinja2 template:
@router.get("/", status_code=200, response_class=HTMLResponse)
async def root( request: Request ):
    
    post_id = 1
    blogpost = await blogposts.read_blogpost(post_id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    blogPostList = await blogposts.read_all_blogposts()
    
    # print(f"root GET, blogPostList is {blogPostList[0]}")
    
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "contentPost": blogpost, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve login page thru a Jinja2 template:
@router.get("/login", status_code=200, response_class=HTMLResponse)
async def root( request: Request ):

    blogPostList = await blogposts.read_all_blogposts()
    
    # print(f"root GET, blogPostList is {blogPostList[0]}")
    
    return TEMPLATES.TemplateResponse(
        "login.html",
        {"request": request, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve the requested page thru a Jinja2 template:
@router.get("/blog/{post_id}", status_code=200, response_class=HTMLResponse)
async def root( request: Request, post_id: int ):
    
    # blogpost = await crud.get_blogpost(post_id)
    blogpost = await blogposts.read_blogpost(post_id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    blogPostList = await blogposts.read_all_blogposts()
    # print(f"root GET, blogpost is \n{blogpost.id}")
    
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "contentPost": blogpost, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve with an editor on it thru a template:
@router.get("/Editor/{post_id}", status_code=200, response_class=HTMLResponse)
async def root( request: Request, post_id: int ):
    
    blogpost = await crud.get_blogpost(post_id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "editor.html",
        {"request": request, "contentPost": blogpost, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# and finally include the html routes in the app:
app.include_router(router)

