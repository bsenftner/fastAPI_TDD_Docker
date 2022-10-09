from app.api.models import NoteSchema, BlogPostSchema
from app.db import notes, blogposts, database

from sqlalchemy import asc

# -----------------------------------------------------------------------------------------
# for creating new notes
async def post_note(payload: NoteSchema):
    # Creates a SQLAlchemy insert object expression query
    query = notes.insert().values(title=payload.title, description=payload.description)
    # Executes the query and returns the generated ID
    return await database.execute(query=query)

# -----------------------------------------------------------------------------------------
# for getting notes:
async def get_note(id: int):
    query = notes.select().where(id == notes.c.id)
    return await database.fetch_one(query=query)

# -----------------------------------------------------------------------------------------
# returns all notes:
async def get_all_notes():
    query = notes.select().order_by(asc(notes.c.id))
    return await database.fetch_all(query=query)

# -----------------------------------------------------------------------------------------
# update a note:
async def put_note(id: int, payload: NoteSchema):
    query = (
        notes
        .update()
        .where(id == notes.c.id)
        .values(title=payload.title, description=payload.description)
        .returning(notes.c.id)
    )
    return await database.execute(query=query)

# -----------------------------------------------------------------------------------------
# delete a note:
async def delete_note(id: int):
    query = notes.delete().where(id == notes.c.id)
    return await database.execute(query=query)



# -----------------------------------------------------------------------------------------
# for creating new blogposts
async def post_blogpost(payload: BlogPostSchema):
    # Creates a SQLAlchemy insert object expression query
    query = blogposts.insert().values(title=payload.title, description=payload.description)
    # Executes the query and returns the generated ID
    return await database.execute(query=query)

# -----------------------------------------------------------------------------------------
# for getting blogposts:
async def get_blogpost(id: int):
    query = blogposts.select().where(id == blogposts.c.id)
    return await database.fetch_one(query=query)

# -----------------------------------------------------------------------------------------
# returns all blogposts:
async def get_all_blogposts():
    query = blogposts.select().order_by(asc(blogposts.c.id))
    return await database.fetch_all(query=query)

# -----------------------------------------------------------------------------------------
# update a blogposts:
async def put_blogpost(id: int, payload: BlogPostSchema):
    query = (
        blogposts
        .update()
        .where(id == blogposts.c.id)
        .values(title=payload.title, description=payload.description)
        .returning(blogposts.c.id)
    )
    return await database.execute(query=query)

# -----------------------------------------------------------------------------------------
# delete a blogpost:
async def delete_blogpost(id: int):
    query = blogposts.delete().where(id == blogposts.c.id)
    return await database.execute(query=query)
