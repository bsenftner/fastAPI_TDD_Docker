
from fastapi import FastAPI, APIRouter, HTTPException, Request, status, Depends, BackgroundTasks
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import json   
from app.api.models import NoteSchema

from pathlib import Path

from jose import jwt
from datetime import datetime
from starlette.responses import RedirectResponse

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
from app.api.models import User, ContactMsg, BlogPostSchema
from app.api.users import get_current_active_user, user_has_role
from app.send_email import send_email_async, send_email_background
from app.api.crud import post_note, get_note_by_title, get_note

# generate our "app"
app = FastAPI(title="FastAPI_TDD_Docker (& postgresql): BlogPosts & (Data) Notes", openapi_url="/openapi.json")

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

# ensure site_config exists in the db:
async def initialize_database_data( ):
    print('looking for site_config...')
    note = await get_note_by_title('site_config')
    if not note:
        print('site_config not found, creating...')
        data = { "protect_contact": True }
        
        dataP = json.dumps(data) # dump to string
        
        note = NoteSchema(title="site_config",
                          description = "configuration data for admins",
                          data=dataP
                         )
        id = await post_note( payload=note, owner=1)
        print(f"created site_config with id {id}.")
    else:
        print(f"Loaded site config: {note.data}")
        
        note.data = json.loads(note.data)
        
        print(f"site config recovered: {note.data}")
    # ensure initial blog post exists
    blogpost = await crud.get_blogpost(1)
    if not blogpost:
        first_blogpost_payload = BlogPostSchema(title="hello", description="<p>world</p>")
        id = await crud.post_blogpost(first_blogpost_payload,1)
        print(f"created first blog post with id {id}.")
    else:
        print(f"first blog post title is '{blogpost.title}'")
        
# setup handler for application start that inits the db connection: 
@app.on_event("startup")
async def startup():
    await database.connect()
    await initialize_database_data()
    
    

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
        { "request": request, 
          "contentPost": blogpost, 
          "frags": FRAGS, 
          "blogPosts": blogPostList }, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve blog post page with an editor on it thru a template:
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
# serve a user profile page thru a template:
@router.get("/Settings", status_code=200, response_class=HTMLResponse)
async def user_settings_page( request: Request, current_user: User = Depends(get_current_active_user) ):
    
    # default info available to the page: 
    page_data = {
        'username': current_user.username,
        'email': current_user.email,
    }
    
    # list of blog posts:
    blogPostList = await blogposts.read_all_blogposts()
    
    # if an ordinary user get user_page, if admin get admin_page: 
    page = 'user_page.html'
    if user_has_role( current_user, "admin"):
        page = 'admin_page.html'
        
        # get site_config note to add to the admin page 
        # more items that can be changed:
        site_config = await get_note(1) # site_config has id 1
        if site_config:
            site_config.data = json.loads(site_config.data)
            page_data.update(site_config.data)
       
    return TEMPLATES.TemplateResponse(
        page,
        {"request": request, "data": page_data, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    

    
# ------------------------------------------------------------------------------------------------------------------
@router.get('/send-email/asynchronous')
async def send_email_asynchronous(current_user: User = Depends(get_current_active_user)):
    await send_email_async('bsenftner@earthlink.net',
                           { 'msg': { 'subject': 'the title', 'body': 'this is the body'}},
                           'basic_email.html')
    return 'Success'
  

    
# ------------------------------------------------------------------------------------------------------------------
@router.post('/send-email/contact', response_model=ContactMsg)
async def send_contact_email_asynchronous(msg: ContactMsg):
    await send_email_async('bsenftner@earthlink.net', 
                           { 'msg': { 'subject': msg.subject, 'body': msg.msg}},
                           'basic_email.html')
    return msg

# ------------------------------------------------------------------------------------------------------------------
@router.get('/send-email/backgroundtasks')
def send_email_backgroundtasks(background_tasks: BackgroundTasks, current_user: User = Depends(get_current_active_user)):
    send_email_background(background_tasks, 
                          'Hello World',   
                          'someemail@gmail.com', 
                          { 'msg': { 'subject': 'the title', 'body': 'this is the body'}})
    return 'Success'

  
        
# ------------------------------------------------------------------------------------------------------------------
# serve an auth requiring contact page with an editor on it thru a template:
@router.get("/Contactp", status_code=200, response_class=HTMLResponse)
async def contact_page_protected( request: Request, 
                                  current_user: User = Depends(get_current_active_user) ):
            
    # print("contact_page_protected: rendering template")
    
    email = {
        'subject': 'your subject',
        'msg': 'your message'
    }

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "contact.html",
        {"request": request, 
         "contentPost": email, 
         "frags": FRAGS, 
         "blogPosts": blogPostList}, 
    )

# ------------------------------------------------------------------------------------------------------------------
# serve a contact page with an editor on it thru a template:
@router.get("/Contact", status_code=200, response_class=HTMLResponse)
async def contact_page( request: Request ):
    
    # get site_config to check if current endpoint should be protected:
    site_config = await get_note(1) # site_config has id 1
    if site_config:
        # print(f"raw site_config.data is {site_config.data}")
        site_config.data = json.loads(site_config.data)
        # print(f"recovered site_config.data is {site_config.data}")
        if site_config.data["protect_contact"]:
            # print("redirecting!")
            response = RedirectResponse(url='/Contactp') 
            return response
        
    email_json = {
        'subject': 'your subject',
        'msg': 'your message',
    }

    blogPostList = await blogposts.read_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "contact.html",
        { "request": request, 
          "contentPost": email_json, 
          "frags": FRAGS, 
          "blogPosts": blogPostList
        }, 
    )


# and include these locally implemented html routes in the app:
app.include_router(router)

