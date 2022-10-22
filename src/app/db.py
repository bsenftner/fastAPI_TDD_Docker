import os

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


DATABASE_URL = os.getenv("DATABASE_URL")


# SQLAlchemy
engine = create_engine(DATABASE_URL) # , future=True) adding the future parameter enables SQLAlchemy 2.0 syntax

# metadata is a container for tables
metadata = MetaData()

notes = Table(
    "notes",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("title", String(50)),
    Column("description", String(50)),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)

blogposts = Table(
    "blogposts",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("owner", Integer, index=True),
    Column("title", String),
    Column("description", String),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, index=True),
    Column("email", String(80), index=True),
    Column("roles", String),
    Column("hashed_password", String(80)),
    Column("verify_code", String(16)),
    Column("created_date", DateTime, default=func.now(), nullable=False),
)


# databases query builder
database = Database(DATABASE_URL)

    
# create db tables if they don't already exist:
metadata.create_all(engine)

