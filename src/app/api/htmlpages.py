from fastapi import APIRouter, HTTPException, Request, status, Depends
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates

from starlette.responses import RedirectResponse

import json

from app import config
from app.api import crud, users
from app.api.models import User, ContactMsg
from app.send_email import send_email_async

# page_frag.py contains common page fragments, like .header & .footer.
# This is passed to page templates for repeated use of common html fragments: 
from app.page_frags import FRAGS 


TEMPLATES = Jinja2Templates(directory=str(config.get_base_path() / "templates"))


# define a router for the html returning endpoints: 
router = APIRouter()


   
# ------------------------------------------------------------------------------------------------------------------
# added to get favicon served:
favicon_path = config.get_base_path() / 'favicon.ico'
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

    blogPostList = await crud.get_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "home.html",
        {"request": request, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    

# ------------------------------------------------------------------------------------------------------------------
# serve registration page thru a Jinja2 template:
@router.get("/register", status_code=status.HTTP_201_CREATED, response_class=HTMLResponse)
async def register( request: Request ):

    blogPostList = await crud.get_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "register.html",
        {"request": request, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve login page thru a Jinja2 template:
@router.get("/login", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def login( request: Request ):

    blogPostList = await crud.get_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "login.html",
        {"request": request, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    

# ------------------------------------------------------------------------------------------------------------------
# serve the requested page thru a Jinja2 template:
@router.get("/blog/{post_id}", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def blogPage( request: Request, post_id: int ):
    
    blogpost = await crud.get_blogpost(post_id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    blogPostList = await crud.get_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "index.html",
        { "request": request, 
          "contentPost": blogpost, 
          "frags": FRAGS, 
          "blogPosts": blogPostList }, 
    )
    

# ------------------------------------------------------------------------------------------------------------------
# serve blog post page with an editor on it thru a template:
@router.get("/Editor/{post_id}", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def editor( request: Request, post_id: int, current_user: User = Depends(users.get_current_active_user) ):
    
    blogpost = await crud.get_blogpost(post_id)
    if not blogpost:
        raise HTTPException(status_code=404, detail="BlogPost not found")

    blogPostList = await crud.get_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "editor.html",
        {"request": request, "contentPost": blogpost, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
# ------------------------------------------------------------------------------------------------------------------
# serve a user profile page thru a template:
@router.get("/Settings", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def user_settings_page( request: Request, current_user: User = Depends(users.get_current_active_user) ):
    
    # default info available to the page: 
    page_data = {
        'username': current_user.username,
        'email': current_user.email,
        'roles': current_user.roles,
    }
    
    # list of blog posts:
    blogPostList = await crud.get_all_blogposts()
    
    # if an ordinary user get user_page, if admin get admin_page: 
    page = 'user_page.html'
    if users.user_has_role( current_user, "admin"):
        page = 'admin_page.html'
        
        # get site_config note to add to the admin page 
        # more items that can be changed:
        site_config = await crud.get_note(1) # site_config has id 1
        if site_config:
            site_config.data = json.loads(site_config.data)
            page_data.update(site_config.data)
       
    return TEMPLATES.TemplateResponse(
        page,
        {"request": request, "data": page_data, "frags": FRAGS, "blogPosts": blogPostList}, 
    )
    
     
    
# ------------------------------------------------------------------------------------------------------------------
@router.post('/send-email/contact', response_model=ContactMsg)
async def send_contact_email_asynchronous(msg: ContactMsg):
    await send_email_async('bsenftner@earthlink.net', 
                           { 'msg': { 'subject': msg.subject, 'body': msg.msg}},
                           'basic_email.html')
    return msg

# ------------------------------------------------------------------------------------------------------------------
# serve an auth requiring contact page with an editor on it thru a template:
@router.get("/Contactp", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def contact_page_protected( request: Request, 
                                  current_user: User = Depends(users.get_current_active_user) ):
            
    # print("contact_page_protected: rendering template")
    
    email = {
        'subject': 'your subject',
        'msg': 'your message'
    }

    blogPostList = await crud.get_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "contact.html",
        {"request": request, 
         "contentPost": email, 
         "frags": FRAGS, 
         "blogPosts": blogPostList}, 
    )

# ------------------------------------------------------------------------------------------------------------------
# serve a contact page with an editor on it thru a template:
@router.get("/Contact", status_code=status.HTTP_200_OK, response_class=HTMLResponse)
async def contact_page( request: Request ):
    
    # get site_config to check if current endpoint should be protected:
    site_config = await crud.get_note(1) # site_config has id 1
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

    blogPostList = await crud.get_all_blogposts()
    
    return TEMPLATES.TemplateResponse(
        "contact.html",
        { "request": request, 
          "contentPost": email_json, 
          "frags": FRAGS, 
          "blogPosts": blogPostList
        }, 
    )
