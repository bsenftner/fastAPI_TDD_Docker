from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware 

from app import config
from app.db import database
from app.api import blogposts, notes, ping, users_htmlpages, video, htmlpages




# generate our "app"
app = FastAPI(title="FastAPI_TDD_Docker (& postgresql): BlogPosts & Data Notes", openapi_url="/openapi.json")

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
app.mount("/static", StaticFiles(directory=str(config.get_base_path() / "static")), name="static") 

# isolate these activities into their own file:
from app.startup import initialize_database_data
#
# setup handler for application start that inits the db connection: 
@app.on_event("startup")
async def startup():
    await database.connect()
    await initialize_database_data()
#  
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
app.include_router(blogposts.router, prefix="/blogposts", tags=["blog-posts"])

# install the blogposts router into our app with a prefix & tag too:
app.include_router(video.router, prefix="/video", tags=["video"])

# install the usershtmlpages router into our app with tag too:
app.include_router(users_htmlpages.router, tags=["user-pages"])

# install the html pages router into our app with tag too:
app.include_router(htmlpages.router, tags=["general-pages"])



