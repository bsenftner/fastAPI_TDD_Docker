from typing import List
from sqlalchemy import asc 

from app.api.models import NoteSchema, BlogPostSchema, UserReg

from app.db import DatabaseMgr, get_database_mgr
# from app.db import notes_tb, blogposts_tb, users_tb, database
 

from app.api.models import UserInDB, BlogPostDB, NoteDB


# -----------------------------------------------------------------------------------------
# for creating new notes
async def post_note(payload: NoteSchema, owner: int):
    db_mgr = get_database_mgr()
    # Creates a SQLAlchemy insert object expression query
    query = db_mgr.get_notes_table().insert().values(title=payload.title, 
                                                     description=payload.description,
                                                     data=payload.data,
                                                     owner=owner)
    # Executes the query and returns the generated ID
    return await db_mgr.get_db().execute(query=query)

# -----------------------------------------------------------------------------------------
# for getting notes:
async def get_note(id: int) -> NoteDB:
    db_mgr = get_database_mgr()
    query = db_mgr.get_notes_table().select().where(id == db_mgr.get_notes_table().c.id)
    return await db_mgr.get_db().fetch_one(query=query)

# -----------------------------------------------------------------------------------------
# for getting notes by their title:
async def get_note_by_title(title: str) -> NoteDB:
    db_mgr = get_database_mgr()
    query = db_mgr.get_notes_table().select().where(title == db_mgr.get_notes_table().c.title)
    return await db_mgr.get_db().fetch_one(query=query)

# -----------------------------------------------------------------------------------------
# returns all notes:
async def get_all_notes() -> List[NoteDB]:
    db_mgr = get_database_mgr()
    query = db_mgr.get_notes_table().select().order_by(asc(db_mgr.get_notes_table().c.id))
    return await db_mgr.get_db().fetch_all(query=query)

# -----------------------------------------------------------------------------------------
# update a note:
async def put_note(id: int, payload: NoteSchema, owner: int):
    db_mgr = get_database_mgr()
    query = (
        db_mgr.get_notes_table()
        .update()
        .where(id == db_mgr.get_notes_table().c.id)
        .values(title=payload.title, 
                description=payload.description, 
                data=payload.data,
                owner=owner)
        .returning(db_mgr.get_notes_table().c.id)
    )
    return await db_mgr.get_db().execute(query=query)

# -----------------------------------------------------------------------------------------
# delete a note:
async def delete_note(id: int):
    db_mgr = get_database_mgr()
    query = db_mgr.get_notes_table().delete().where(id == db_mgr.get_notes_table().c.id)
    return await db_mgr.get_db().execute(query=query)



# -----------------------------------------------------------------------------------------
# for creating new blogposts
async def post_blogpost(payload: BlogPostSchema, user_id: int):
    db_mgr = get_database_mgr()
    # Creates a SQLAlchemy insert object expression query
    query = db_mgr.get_blogposts_table().insert().values(owner=user_id, 
                                                         title=payload.title, 
                                                         description=payload.description)
    # Executes the query and returns the generated ID
    return await db_mgr.get_db().execute(query=query)

# -----------------------------------------------------------------------------------------
# for getting blogposts:
async def get_blogpost(id: int) -> BlogPostDB:
    db_mgr = get_database_mgr()
    query = db_mgr.get_blogposts_table().select().where(id == db_mgr.get_blogposts_table().c.id)
    return await db_mgr.get_db().fetch_one(query=query)

# -----------------------------------------------------------------------------------------
# returns all blogposts:
async def get_all_blogposts():
    db_mgr = get_database_mgr()
    query = db_mgr.get_blogposts_table().select().order_by(asc(db_mgr.get_blogposts_table().c.id))
    return await db_mgr.get_db().fetch_all(query=query)

# -----------------------------------------------------------------------------------------
# update a blogposts:
async def put_blogpost(id: int, payload: BlogPostSchema):
    db_mgr = get_database_mgr()
    query = (
        db_mgr.get_blogposts_table()
        .update()
        .where(id == db_mgr.get_blogposts_table().c.id)
        .values(title=payload.title, description=payload.description)
        .returning(db_mgr.get_blogposts_table().c.id)
    )
    return await db_mgr.get_db().execute(query=query)

# -----------------------------------------------------------------------------------------
# delete a blogpost:
async def delete_blogpost(id: int):
    db_mgr = get_database_mgr()
    query = db_mgr.get_blogposts_table().delete().where(id == db_mgr.get_blogposts_table().c.id)
    return await db_mgr.get_db().execute(query=query)




# -----------------------------------------------------------------------------------------
# for creating new users:
async def post_user(user: UserReg, 
                    hashed_password: str,
                    verify_code: str,
                    roles: str):
    '''crud action to create a new user via PRE-VALIDATED data'''
    db_mgr = get_database_mgr()
    query = db_mgr.get_users_table().insert().values( username=user.username, 
                                                      hashed_password=hashed_password,
                                                      verify_code=verify_code,
                                                      email=user.email,
                                                      roles=roles )
    # Executes the query and returns the generated ID
    return await db_mgr.get_db().execute(query)
    

# -----------------------------------------------------------------------------------------
# a few methods for getting users:
async def get_user_by_id(id: int):
    db_mgr = get_database_mgr()
    query = db_mgr.get_users_table().select().where(id == db_mgr.get_users_table().c.id)
    return await db_mgr.get_db().fetch_one(query=query)

async def get_user_by_name(username: str):
    db_mgr = get_database_mgr()
    query = db_mgr.get_users_table().select().where(db_mgr.get_users_table().c.username == username)
    return await db_mgr.get_db().fetch_one(query)


async def get_user_by_email(email: str):
    db_mgr = get_database_mgr()
    query = db_mgr.get_users_table().select().where(db_mgr.get_users_table().c.email == email)
    return await db_mgr.get_db().fetch_one(query)

# -----------------------------------------------------------------------------------------
# update a user passed an user id and an updated UserInDB. 
# Note: the id field in the UserInDB is ignored. 
async def put_user(id: int, user: UserInDB):
    db_mgr = get_database_mgr()
    query = (
        db_mgr.get_users_table()
        .update()
        .where(id == db_mgr.get_users_table().c.id)
        .values( username=user.username, 
                 hashed_password=user.hashed_password,
                 verify_code=user.verify_code,
                 email=user.email,
                 roles=user.roles
               ).returning(db_mgr.get_users_table().c.id)
        .returning(db_mgr.get_users_table().c.id)
    )
    return await db_mgr.get_db().execute(query=query)

# -----------------------------------------------------------------------------------------
# note: there is no user delete, that is accomplished by disabling a user. 
# A user is disabled by adding the "disabled" to their "roles" db field. 