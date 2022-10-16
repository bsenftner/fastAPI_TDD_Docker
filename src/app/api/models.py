from typing import Union
from pydantic import BaseModel, Field, EmailStr, constr

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



# an access token used by authentication
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    
class User(BaseModel):
    username: str
    email: Union[EmailStr, None] = None
    roles: Union[str, None] = None
    disabled: Union[bool, None] = None
    
class UserInDB(User):
    id: int
    hashed_password: str

class UserReg(BaseModel):
    username: str
    password: constr(min_length=12)
    email: Union[EmailStr, None] = None
    
class UserPublic(BaseModel):
    username: str
    id: int
    roles: Union[str, None] = None
    email: Union[EmailStr, None] = None
    
    