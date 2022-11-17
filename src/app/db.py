from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.sql import func

from sqlalchemy.orm import relationship

from databases import Database

from app.config import get_settings

from functools import lru_cache


# ----------------------------------------------------------------------------------------------
class DatabaseMgr:
    def __init__(self):
        # SQLAlchemy
        url = get_settings().DATABASE_URL
        print(f"DatabaseMgr:__init__:: database_url = {url}")
        if url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
            print(f"DatabaseMgr:__init__:: tweaked database_url = {url}")
        #
        self.engine = create_engine(url) # , future=True) adding the future parameter enables SQLAlchemy 2.0 syntax

        # metadata is a container for tables
        self.metadata = MetaData()

        self.blogposts_tb = Table(
            "blogposts",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("owner", Integer, index=True),
            Column("title", String),
            Column("description", String),
            Column("tags", String),
            Column("created_date", DateTime, default=func.now(), nullable=False),
        )

        self.users_tb = Table(
            "users",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("username", String, index=True),
            Column("email", String(80), index=True),
            Column("roles", String),
            Column("hashed_password", String(80)),
            Column("verify_code", String(16)),
            Column("created_date", DateTime, default=func.now(), nullable=False),
        )

        self.notes_tb = Table(
            "notes",
            self.metadata,
            Column("id", Integer, primary_key=True),
            Column("owner", Integer, index=True),
            Column("title", String, index=True),
            Column("description", String),      # describe the data here
            Column("data", String),             # data saved as string of encoded json
            Column("created_date", DateTime, default=func.now(), nullable=False),
        )

        # databases query builder
        self.database = Database(get_settings().DATABASE_URL)

        # create db tables if they don't already exist:
        self.metadata.create_all(self.engine)
        
        
    def get_db(self):
        return self.database
        
    def get_blogposts_table(self):
        return self.blogposts_tb
        
    def get_users_table(self):
        return self.users_tb
        
    def get_notes_table(self):
        return self.notes_tb


# ----------------------------------------------------------------------------------------------
@lru_cache()
def get_database_mgr() -> DatabaseMgr:
    database_mgr = DatabaseMgr()
    return database_mgr




