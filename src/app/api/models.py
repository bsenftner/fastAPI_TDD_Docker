from typing import Union
from pydantic import BaseModel, Field

# create a "Pydantic Model" of the data we want to maintain in the database
# by inheriting from BaseModel. This inherits data parsing and validation 
# such that fields of the model are guaranteed to be these types when filled 
# with payloads for creating and updating Notes. 
class NoteSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=50)
    description: str = Field(..., min_length=3, max_length=50)

# A "Note" in the database is simply an id plus our NoteSchema: 
class NoteDB(NoteSchema):
    id: int



# seeing if a separate table can be defined under this code/app structure:
class BlogPostSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: str = Field(..., min_length=3, max_length=16384)

# A "BlogPost" in the database is simply an id plus our BlogPostSchema: 
class BlogPostDB(BlogPostSchema):
    id: int



