
from fastapi import FastAPI, APIRouter, HTTPException, Request, status, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

from pathlib import Path

# page_frag.py contains common page fragments, like .header & .footer.
# This is passed to page templates for repeated use of common html fragments: 
from app.page_frags import FRAGS 

# Project Directories
BASE_PATH = Path(__file__).resolve().parent
TEMPLATES = Jinja2Templates(directory=str(BASE_PATH / "templates")) 

from dotenv import dotenv_values 
envConfig = dotenv_values(str(BASE_PATH / ".env"))  
'''
print('envConfig is')
for key, value in envConfig.items():
    print(key, ' : ', value)
'''

from app.db import database
from app.api import blogposts, notes, users, ping, crud 
from app.api.models import User, ContactMsg
from app.api.users import get_current_active_user
from app.send_email import send_email_async, send_email_background


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

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "home.html",
        {"request": request, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve registration page thru a Jinja2 template:
@router.get("/register", status_code=status.HTTP_201_CREATED, response_class=HTMLResponse)
async def register( request: Request ):

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "register.html",
        {"request": request, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve login page thru a Jinja2 template:
@router.get("/login", status_code=200, response_class=HTMLResponse)
async def login( request: Request ):

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "login.html",
        {"request": request, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve the requested page thru a Jinja2 template:
@router.get("/blog/{post_id}", status_code=200, response_class=HTMLResponse)
async def blogPage( request: Request, post_id: int ):
    
    blogpost = await blogposts.read_blogpost(post_id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "index.html",
        {"request": request, "contentPost": blogpost, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve a contact page with an editor on it thru a template:
@router.get("/Contact", status_code=200, response_class=HTMLResponse)
async def contact( request: Request ):
    
    email = {
        'subject': 'your subject',
        'msg': 'your message'
    }

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "contact.html",
        {"request": request, "contentPost": email, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve with an editor on it thru a template:
@router.get("/Editor/{post_id}", status_code=200, response_class=HTMLResponse)
async def editor( request: Request, post_id: int, current_user: User = Depends(get_current_active_user) ):
    
    blogpost = await crud.get_blogpost(post_id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "editor.html",
        {"request": request, "contentPost": blogpost, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    

    
# ------------------------------------------------------------------------------------------------------------------
@router.get('/send-email/asynchronous')
async def send_email_asynchronous(current_user: User = Depends(get_current_active_user)):
    await send_email_async('Hello World','bsenftner@earthlink.net',
    { 'body': { 'title': 'the title', 'name':'this is the body'}})
    return 'Success'
  

    
# ------------------------------------------------------------------------------------------------------------------
@router.post('/send-email/contact', response_model=ContactMsg)
async def send_contact_email_asynchronous(msg: ContactMsg):
    
    await send_email_async(msg.subject,'bsenftner@earthlink.net',
    { 'body': { 'title': msg.subject, 'name': msg.msg}})
    return msg

# ------------------------------------------------------------------------------------------------------------------
@router.get('/send-email/backgroundtasks')
def send_email_backgroundtasks(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_active_user)):
    send_email_background(background_tasks, 'Hello World',   
    'someemail@gmail.com', {'title': 'Hello World', 'name':       'John Doe'})
    return 'Success'



# and finally include these locally implemented html routes in the app:
app.include_router(router)