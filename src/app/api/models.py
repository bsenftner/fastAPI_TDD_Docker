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



# basic "blog post":
class BlogPostSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=80)
    description: str = Field(..., min_length=3, max_length=16384)

# A "BlogPost" in the database is simply an id plus our BlogPostSchema: 
class BlogPostDB(BlogPostSchema):
    id: int
    owner: int



# an access token used by authentication
class Token(BaseModel):
    access_token: str
    token_type: str
    refresh_token: str
    
# a user 
class User(BaseModel):
    username: str
    email: EmailStr
    roles: str
    # disabled: Union[bool, None] = None
    # email: Union[EmailStr, None] = None
    # roles: Union[str, None] = None

    
# a user in the dabase
class UserInDB(User):
    id: int
    verify_code: str
    hashed_password: str

# info for user registration
class UserReg(BaseModel):
    username: str
    password: constr(min_length=12)
    email: EmailStr
    # email: Union[EmailStr, None] = None
    
# info returned from a user query
class UserPublic(BaseModel):
    username: str
    id: int
    roles: str
    email: EmailStr
    # roles: Union[str, None] = None
    # email: Union[EmailStr, None] = None
    
    
# info posted by a user as their email verification code:
class VerifyEmailPayload(BaseModel):
    code: str
    
    
# info posted by a user as a Contact the website email message:
class ContactMsg(BaseModel):
    subject: str
    msg: str