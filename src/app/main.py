from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware 

from app import config
from app.db import DatabaseMgr, get_database_mgr
from app.api import blogposts, notes, ping, users_htmlpages, video, htmlpages, upload, backups


# generate our "app"
def create_application() -> FastAPI:

    application = FastAPI(title="FastAPI_TDD_Docker (& postgresql): BlogPosts & Data Notes", openapi_url="/openapi.json")

    # add CORS handling: 
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,
    )
    
    # enable automatic serving of contents of "static" directory: 
    application.mount("/static", StaticFiles(directory=str(config.get_base_path() / "static")), name="static") 


    
    
    # isolate these activities into their own file:
    from app.startup import initialize_database_data
    #
    # setup handler for application start that inits the db connection: 
    @application.on_event("startup")
    async def startup():
        db_mgr: DatabaseMgr = get_database_mgr()
        await db_mgr.get_db().connect()
        await initialize_database_data()
    #     
    # setup handler for application shutdown that disconnects the db: 
    @application.on_event("shutdown")
    async def shutdown():
        db_mgr: DatabaseMgr = get_database_mgr()
        await db_mgr.get_db().disconnect()

    # install the ping router into our app:
    application.include_router(ping.router)

    # install the notes router into our app;
    # note the prefix URL along with the "notes" tag, 
    # the prefix places the routes defined by notes.router after "/notes",
    # these are also used by OpenAPI (for grouping operations).
    application.include_router(notes.router, prefix="/notes", tags=["notes"])

    # install the blogposts router into our app with a prefix & tag too:
    application.include_router(blogposts.router, prefix="/blogposts", tags=["blog-posts"])

    # install the video router into our app with a prefix & tag too:
    application.include_router(video.router, prefix="/video", tags=["video"])

    # install the upload router into our app with a prefix & tag too:
    application.include_router(upload.router, prefix="/upload", tags=["upload"])

    # install the backups router into our app with a prefix & tag too:
    application.include_router(backups.router, prefix="/backups", tags=["backups"])

    # install the users htmlpages router into our app with tag too:
    application.include_router(users_htmlpages.router, tags=["user-pages"])

    # install the html pages router into our app with tag too:
    application.include_router(htmlpages.router, tags=["general-pages"])
    
    return application


# and instantiate it:
app = create_application()

