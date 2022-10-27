from app.api.models import NoteSchema, BlogPostSchema
from app.db import notes_tb, blogposts_tb, database

from sqlalchemy import asc  

# -----------------------------------------------------------------------------------------
# for creating new notes
async def post_note(payload: NoteSchema, owner: int):
    # Creates a SQLAlchemy insert object expression query
    query = notes_tb.insert().values(title=payload.title, 
                                  description=payload.description,
                                  data=payload.data,
                                  owner=owner)
    # Executes the query and returns the generated ID
    return await database.execute(query=query)

# -----------------------------------------------------------------------------------------
# for getting notes:
async def get_note(id: int):
    query = notes_tb.select().where(id == notes_tb.c.id)
    return await database.fetch_one(query=query)

# -----------------------------------------------------------------------------------------
# for getting notes by their title:
async def get_note_by_title(title: str):
    query = notes_tb.select().where(title == notes_tb.c.title)
    return await database.fetch_one(query=query)

# -----------------------------------------------------------------------------------------
# returns all notes:
async def get_all_notes():
    query = notes_tb.select().order_by(asc(notes_tb.c.id))
    return await database.fetch_all(query=query)

# -----------------------------------------------------------------------------------------
# update a note:
async def put_note(id: int, payload: NoteSchema, owner: int):
    query = (
        notes_tb
        .update()
        .where(id == notes_tb.c.id)
        .values(title=payload.title, 
                description=payload.description, 
                data=payload.data,
                owner=owner)
        .returning(notes_tb.c.id)
    )
    return await database.execute(query=query)

# -----------------------------------------------------------------------------------------
# delete a note:
async def delete_note(id: int):
    query = notes_tb.delete().where(id == notes_tb.c.id)
    return await database.execute(query=query)



# -----------------------------------------------------------------------------------------
# for creating new blogposts
async def post_blogpost(payload: BlogPostSchema, user_id: int):
    # Creates a SQLAlchemy insert object expression query
    query = blogposts_tb.insert().values(owner=user_id, 
                                      title=payload.title, 
                                      description=payload.description)
    # Executes the query and returns the generated ID
    return await database.execute(query=query)

# -----------------------------------------------------------------------------------------
# for getting blogposts:
async def get_blogpost(id: int):
    query = blogposts_tb.select().where(id == blogposts_tb.c.id)
    return await database.fetch_one(query=query)

# -----------------------------------------------------------------------------------------
# returns all blogposts:
async def get_all_blogposts():
    query = blogposts_tb.select().order_by(asc(blogposts_tb.c.id))
    return await database.fetch_all(query=query)

# -----------------------------------------------------------------------------------------
# update a blogposts:
async def put_blogpost(id: int, payload: BlogPostSchema):
    query = (
        blogposts_tb
        .update()
        .where(id == blogposts_tb.c.id)
        .values(title=payload.title, description=payload.description)
        .returning(blogposts_tb.c.id)
    )
    return await database.execute(query=query)

# -----------------------------------------------------------------------------------------
# delete a blogpost:
async def delete_blogpost(id: int):
    query = blogposts_tb.delete().where(id == blogposts_tb.c.id)
    return await database.execute(query=query)
