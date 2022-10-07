from fastapi import FastAPI

from app.api import blogposts, notes, ping
from app.db import engine, database, metadata

metadata.create_all(engine)

app = FastAPI(title="FastAPI_TDD_Docker : Notes and BlogPosts", openapi_url="/openapi.json")


@app.on_event("startup")
async def startup():
    await database.connect()

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


app.include_router(blogposts.router, prefix="/blogposts", tags=["blogposts"])
